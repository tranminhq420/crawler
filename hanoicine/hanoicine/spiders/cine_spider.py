from pathlib import Path
# import json
import scrapy
from ..items import HanoicineItem


class CineSpider(scrapy.Spider):
    name = "hanoicine"

    def start_requests(self):
        urls = [
            "https://www.bhdstar.vn/lich-chieu/",
            "https://www.bhdstar.vn/lich-chieu/page/2/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for movie in response.css('div.film-col-item'):
            item = HanoicineItem()
            item['id'] = movie.css('h4.title a::attr(data-id)').get()
            item['title'] = movie.css('h4.title a::attr(title)').get(),
            item['age_limit'] = movie.css('span.age-limit::text').get(),
            item['movie_type'] = movie.css('span.type::text').get(),
            item['format'] = movie.css('span.format::text').get(),
            item['genre'] = movie.css('div.cats a::text').get(),
            item['image_url'] = movie.css('div.thumb img::attr(src)').get()
            item['movie_url'] = movie.css(
                'h4.title a::attr(href)').get()
            print(item)
            yield (item)
        filename = f"films.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")
