import scrapy
from scrapy.crawler import CrawlerProcess

class ToradexSpider(scrapy.Spider):
	name = 'toradex'
	allowed_domains = ['developer.toradex.com']
	start_urls = ['https://developer.toradex.com']

	def parse(self, response):
		# Extract the title
		title = response.css('title::text').get()
		
		# Extract the article text, including headings and links
		content = response.css('div.theme-doc-markdown').xpath('./*[self::p or self::h1 or self::h2 or self::h3 or self::h4 or self::h5]')
		article_text = []
		for elem in content:
			if elem.root.tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
				heading = elem.css('::text').get()
				article_text.append(f'\n\n{heading}\n')
			else:
				text = ''.join(elem.xpath('.//text()').getall())
				article_text.append(text)
		article_text = ' '.join(article_text)
		
		# Extract the categories if available (assuming the categories are within certain elements)
		categories = response.css('div.theme-doc-sidebar-container a::text').getall()

		# Only yield data if categories are not empty
		yield {
			'title': title,
			'article_text': article_text,
			'categories': categories,
			'url': response.url
		}

		# Follow internal links
		for href in response.css('a::attr(href)').getall():
			if href.startswith('/') or 'developer.toradex.com' in href:
				next_page = response.urljoin(href)
				yield scrapy.Request(next_page, callback=self.parse)