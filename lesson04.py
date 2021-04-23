from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from auto_youla_parser.spiders.auto_youla_ru import AutoYoulaRuSpider
from pymongo import MongoClient


class Persistor:
    def __init__(self, database_url, database_name, collection_name):
        self._db = MongoClient(database_url).get_database(database_name)
        self._collection = self._db.get_collection(collection_name)

    def persist(self, doc):
        self._collection.insert_one(doc)


if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule("auto_youla_parser.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(
        AutoYoulaRuSpider,
        persistor=Persistor(
            database_url="mongodb://localhost:27017",
            database_name="col-an-methods",
            collection_name="lesson04",
        ),
    )
    crawler_proc.start()
