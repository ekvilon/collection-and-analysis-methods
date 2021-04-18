# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo


class HhParserMongoPipeline:
    def __init__(self, mongo_db_url, mongo_db_name):
        mongo_client = pymongo.MongoClient(mongo_db_url)
        self._db = mongo_client[mongo_db_name]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_db_url=crawler.settings.get("MONGO_DB_URL", "mongodb://127.0.0.1:27017"),
            mongo_db_name=crawler.settings.get("MONGO_DB_NAME", "hh-parser"),
        )

    def process_item(self, item, spider):
        self._db[spider.settings.get("mongo_db_collection_name", spider.name)].insert_one(item)

        return item
