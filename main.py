import json

import scrapy
from scrapy.item import Item, Field
from scrapy.crawler import CrawlerProcess
from itemadapter import ItemAdapter


class QuoteItem(Item):
    author = Field()
    quote = Field()
    tags = Field()


class AuthorItem(Item):
    fullname = Field()
    born_date = Field()
    born_location = Field()
    description = Field()


class SpiderPipLine:
    quotes = []
    authors = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if 'author' in adapter.keys():
            self.quotes.append({
                "author": adapter["author"],
                "quote": adapter["quote"],
                "tags": adapter["tags"]
            })

        if 'fullname' in adapter.keys():
            self.authors.append({
                "fullname": adapter["fullname"],
                "born_date": adapter["born_date"],
                "born_location": adapter["born_location"],
                "description": adapter["description"]
            })
        return item

    def close_spider(self, spider):
        with open('quotes.json', 'w', encoding='utf-8') as file:
            json.dump(self.quotes, file, ensure_ascii=False)

        with open('authors.json', 'w', encoding='utf-8') as file:
            json.dump(self.authors, file, ensure_ascii=False)


class QuotesSpider(scrapy.Spider):
    name = 'authors'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']
    custom_settings = {
        "ITEM_PIPELINES": {
            SpiderPipLine: 300
        }
    }

    def parse(self, response):
        for block_q in response.xpath("/html//div[@class='quote']"):
            quote = block_q.xpath("span[@class='text']/text()").get().strip()
            author = block_q.xpath('span/small[@class="author"]/text()').get().strip()
            tags = block_q.xpath('div[@class="tags"]/a[@class="tag"]/text()').extract()
            yield QuoteItem(author=author, quote=quote, tags=tags)

            url_author = block_q.css('.quote span a').attrib['href']
            yield response.follow(url=url_author, callback=self.parse_author)

        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield response.follow(url=next_link, callback=self.parse)

    def parse_author(self, response):
        body = response.xpath('/html//div[@class="author-details"]')
        fullname = body.xpath('h3[@class="author-title"]/text()').get().strip()
        born_date = body.xpath('p/span[@class="author-born-date"]/text()').get().strip()
        born_location = body.xpath('p/span[@class="author-born-location"]/text()').get().strip()
        description = body.xpath('div[@class="author-description"]/text()').get().strip()
        yield AuthorItem(fullname=fullname, born_date=born_date, born_location=born_location, description=description)


if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(QuotesSpider)
    process.start()
