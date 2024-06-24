import scrapy
from scrapy.crawler import CrawlerProcess
import logging
from bs4 import BeautifulSoup

class DocsSpider(scrapy.Spider):
    name = 'docs'
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
