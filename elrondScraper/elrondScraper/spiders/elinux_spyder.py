import scrapy
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor


class ELinuxSpider(scrapy.Spider):
	name = 'elinux'
	allowed_domains = ['elinux.org']
	start_urls = ['https://elinux.org/Main_Page']

	def parse(self, response):
		# Extract the categories
		categories = response.css('div#mw-normal-catlinks ul li a::text').getall()

		# Only proceed if categories are not empty
		if categories:
			# Extract the title
			title = response.css('h1.firstHeading::text').get()
			
			# Extract the article text, including headings and links
			content = response.css('div.mw-parser-output').xpath('./*[self::p or self::h1 or self::h2 or self::h3 or self::h4 or self::h5]')
			article_text = []
			for elem in content:
				if elem.root.tag in ['h1', 'h2', 'h3', 'h4', 'h5']:
					heading = elem.css('span.mw-headline::text').get()
					article_text.append(f'\n\n{heading}\n')
				else:
					text = ''.join(elem.xpath('.//text()').getall())
					article_text.append(text)
			article_text = ' '.join(article_text)
			
			yield {
				'title': title,
				'article_text': article_text,
				'categories': categories,
				'url': response.url
			}

		# Follow internal links
		for href in response.css('a::attr(href)').getall():
			if href.startswith('/') or 'elinux.org' in href:
				next_page = response.urljoin(href)
				yield scrapy.Request(next_page, callback=self.parse)