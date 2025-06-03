from pathlib import Path
# import json
import scrapy
# from hanoicine.items import HanoicineItem


class RapquocgiaSpider(scrapy.Spider):
    name = "rapquocgia"

    def start_requests(self):
        urls = [
            "https://chieuphimquocgia.com.vn/movies"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # for movie in response.css('div.film-col-item'):
        #     item = HanoicineItem()
        #     item['id'] = movie.css('h4.title a::attr(data-id)').get()
        #     item['title'] = movie.css('h4.title a::attr(title)').get(),
        #     item['age_limit'] = movie.css('span.age-limit::text').get(),
        #     item['movie_type'] = movie.css('span.type::text').get(),
        #     item['format'] = movie.css('span.format::text').get(),
        #     item['genre'] = movie.css('div.cats a::text').get(),
        #     item['image_url'] = movie.css('div.thumb img::attr(src)').get()
        #     item['movie_url'] = movie.css(
        #         'h4.title a::attr(href)').get()
        #     print(item)
        #     yield (item)
        filename = f"rapquocgia.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")
