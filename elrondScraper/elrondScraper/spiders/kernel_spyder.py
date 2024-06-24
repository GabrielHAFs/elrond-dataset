import scrapy
from scrapy.crawler import CrawlerProcess
import logging

class DocsSpider(scrapy.Spider):
	name = 'docs'
	allowed_domains = ['docs.kernel.org', 'docs.u-boot.org']
	start_urls = [
		'https://docs.kernel.org',
		'https://docs.u-boot.org/en/latest/index.html'
	]

	def parse(self, response):
		logging.info(f'Parsing URL: {response.url}')
		
		# Extract the title
		title = response.css('title::text').get()
		
		# Extract the article text, including headings and links
		content = response.css('div.document, div.rst-content')  # Adjusted the main content container selector
		article_text = []
		for elem in content.xpath('.//*'):
			if elem.root.tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
				heading = elem.css('::text').get()
				if heading:
					article_text.append(f'\n\n{heading}\n')
			else:
				text = ''.join(elem.xpath('.//text()').getall())
				if text:
					article_text.append(text)
		article_text = ' '.join(article_text)
		
		# Extract the categories if available
		categories = response.css('ul.current a::text').getall()


		yield {
			'title': title,
			'article_text': article_text,  # Strip leading/trailing whitespace
			'categories': categories,
			'url': response.url
		}

		# Follow internal links
		for href in response.css('a::attr(href)').getall():
			if href.startswith('#'):
				continue
			if href.startswith('/'):
				next_page = response.urljoin(href)
			elif not href.startswith('http'):
				next_page = response.urljoin(href)
			elif 'docs.kernel.org' in href or 'docs.u-boot.org' in href:
				next_page = href
			else:
				continue
			
			# Ensure we don't follow links to the same page or already visited pages
			if next_page != response.url:
				yield scrapy.Request(next_page, callback=self.parse)
