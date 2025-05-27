from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.signalmanager import dispatcher
from scrapy.utils.project import get_project_settings


class TriggerPipeline:
    """Pipeline that triggers another spider after the current one finishes"""

    def __init__(self):
        self.items = []

    def process_item(self, item, spider):
        # Store items for later use by the second spider
        self.items.append(item)
        return item

    def close_spider(self, spider):
        if spider.name == 'hanoicine':
            # Create settings for the second spider
            settings = get_project_settings()

            # Pass collected data to the second spider
            settings.set('PARENT_ITEMS', self.items)

            # Create a new CrawlerProcess for the second spider
            process = CrawlerProcess(settings)

            # Add the second spider to the process
            process.crawl('bhdspider')

            # Start the crawling process
            process.start()  # This is blocking and will start its own reactor
