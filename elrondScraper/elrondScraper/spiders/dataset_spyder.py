import scrapy
import logging
from bs4 import BeautifulSoup

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

class YoctoSpider(scrapy.Spider):
    name = 'yocto'
    allowed_domains = ['docs.yoctoproject.org', 'wiki.yoctoproject.org']
    start_urls = [
        'https://docs.yoctoproject.org',
        'https://wiki.yoctoproject.org/wiki/Main_Page'
    ]

    def parse(self, response):      
        # Determine if it's a documentation or wiki page
        if 'docs.yoctoproject.org' in response.url:
            yield from self.parse_docs(response)
        elif 'wiki.yoctoproject.org' in response.url:
            yield from self.parse_wiki(response)

        # Follow internal links
        for href in response.css('a::attr(href)').getall():
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            if href.startswith('/'):
                next_page = response.urljoin(href)
            elif not href.startswith('http'):
                next_page = response.urljoin(href)
            elif 'docs.yoctoproject.org' in href or 'wiki.yoctoproject.org' in href:
                next_page = href
            else:
                continue
            
            # Ensure we don't follow links to the same page or already visited pages
            if next_page != response.url:
                yield scrapy.Request(next_page, callback=self.parse)
    
    def parse_docs(self, response):
        # Extract the title
        title = response.css('title::text').get()
        
        # Extract the article text, including headings and links
        content = response.css('div.document, div.rst-content').get()
        soup = BeautifulSoup(content, 'html.parser')
        
        article_text = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'li']):
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                heading = tag.get_text(strip=True)
                article_text.append(f'\n\n{heading}\n')
            else:
                text = tag.get_text(strip=True)
                if text:
                    article_text.append(text)
        article_text = ' '.join(article_text)
        
        # Extract the categories if available
        categories = response.css('ul.current a::text').getall()

        # Only yield data if categories are not empty
        item = {
            'title': title,
            'article_text': article_text.strip(),  # Strip leading/trailing whitespace
            'categories': categories,
            'url': response.url
        }
        logging.info(f'Yielding item: {item}')
        yield item

    def parse_wiki(self, response):
        # Extract the title
        title = response.css('h1.firstHeading::text').get()
        
        # Extract the article text, including headings and links
        content = response.css('div.mw-parser-output').get()
        soup = BeautifulSoup(content, 'html.parser')
        
        article_text = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'li']):
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                heading = tag.get_text(strip=True)
                article_text.append(f'\n\n{heading}\n')
            else:
                text = tag.get_text(strip=True)
                if text:
                    article_text.append(text)
        article_text = ' '.join(article_text)
        
        # Extract the categories if available
        categories = response.css('div#mw-normal-catlinks ul li a::text').getall()

        # Only yield data if categories are not empty
        item = {
            'title': title,
            'article_text': article_text.strip(),  # Strip leading/trailing whitespace
            'categories': categories,
            'url': response.url
        }
        logging.info(f'Yielding item: {item}')
        yield item