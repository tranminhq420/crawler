# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class HanoicineItem(Item):
    id = Field()
    title = Field()
    age_limit = Field()
    movie_type = Field()  # Phụ đề/Lồng tiếng
    format = Field()      # 2D/3D
    genre = Field()
    image_url = Field()
    movie_url = Field()


class TheaterItem(Item):
    name = Field()
    address = Field()
    theaterID = Field()


class SessionItem(Item):
    cinemaID = Field()
    sessionID = Field()
    filmID = Field()  # Link sessions to specific films
    time = Field()
    date = Field()
    language = Field()
    format = Field()
    firstClass = Field()


class SeatDataItem(Item):
    session_id = Field()
    cinema_id = Field()
    cinema_name = Field()
    movie_title = Field()
    movie_format = Field()
    movie_language = Field()
    movie_label = Field()
    showtime = Field()
    screen_name = Field()
    screen_number = Field()
    seats_available = Field()
    expire_time = Field()
    tickets_data = Field()
    seats_layout = Field()
    concession_items = Field()
    standard_price = Field()
    vip_price = Field()
    couple_price = Field()
    search_date = Field()
