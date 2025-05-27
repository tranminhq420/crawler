# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from sqlalchemy.orm import sessionmaker
from .models import db_connect, create_table, Film

# class HanoicinePipeline:
#     def process_item(self, item, spider):
#         return item


class SQLAlchemyPipeline:
    """
    Pipeline for storing scraped items in the database
    """

    def __init__(self):
        """
        Initializes database connection and sessionmaker
        Creates tables if they don't exist
        """
        engine = db_connect()
        create_table(engine)
        self.Session = sessionmaker(bind=engine)

    def process_item(self, item, spider):
        """
        Process the item and store in database
        """
        session = self.Session()
        film = Film()

        # Map fields from item to model
        film.title = item.get('title')
        film.age_limit = item.get('age_limit')
        film.movie_type = item.get('movie_type')
        film.format = item.get('format')
        film.genre = item.get('genre')
        film.image_url = item.get('image_url')

        try:
            session.add(film)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

        return item
