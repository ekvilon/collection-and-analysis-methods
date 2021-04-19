from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from avito_parser.spiders.avito_adverts import AvitoAdvertsSpider

# from pymongo import MongoClient


# class Persistor:
#     def __init__(self, database_url, database_name, collection_name):
#         self._db = MongoClient(database_url).get_database(database_name)
#         self._collection = self._db.get_collection(collection_name)
#
#     def persist(self, doc):
#         self._collection.insert_one(doc)


if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule("avito_parser.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(AvitoAdvertsSpider)
    crawler_proc.start()
