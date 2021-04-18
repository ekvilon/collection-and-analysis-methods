from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from hh_parser.spiders.hh_company import HhCompanySpider
from hh_parser.spiders.hh_vacancies import HhVacanciesSpider

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
    crawler_settings.setmodule("hh_parser.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(HhVacanciesSpider)
    crawler_proc.crawl(HhCompanySpider)
    crawler_proc.start()
