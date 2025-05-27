# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class HanoicineItem(Item):
    title = Field()
    age_limit = Field()
    movie_type = Field()  # Phụ đề/Lồng tiếng
    format = Field()      # 2D/3D
    genre = Field()
    image_url = Field()


class MovieItem(Item):
    name = Field()
    location = Field()
    screentime = Field()
    date = Field()
