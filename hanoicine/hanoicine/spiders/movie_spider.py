from pathlib import Path

import scrapy
from ..items import HanoicineItem


class ScreentimeSpider(scrapy.Spider):
    name = "bhdspider"

    def start_requests(self):
        urls = [
            "https://www.bhdstar.vn/lich-chieu/"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for movie in response.css('div.film-col-item'):
            item = HanoicineItem()
            item['title'] = movie.css('h4.title a::attr(title)').get(),
            item['age_limit'] = movie.css('span.age-limit::text').get(),
            item['movie_type'] = movie.css('span.type::text').get(),
            item['format'] = movie.css('span.format::text').get(),
            item['genre'] = movie.css('div.cats a::text').get(),
            item['image_url'] = movie.css('div.thumb img::attr(src)').get()
            print(item)
            yield (item)
        filename = f"films.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")
