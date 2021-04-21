# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo

from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline


class InstagramMongoPipeline:
    def __init__(self, mongo_db_url, mongo_db_name):
        mongo_client = pymongo.MongoClient(mongo_db_url)
        self._db = mongo_client[mongo_db_name]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_db_url=crawler.settings.get("MONGO_DB_URL", "mongodb://127.0.0.1:27017"),
            mongo_db_name=crawler.settings.get("MONGO_DB_NAME", "instagram-parser"),
        )

    def process_item(self, item, spider):
        self._db[spider.settings.get("mongo_db_collection_name", spider.name)].insert_one(item)
        return item


class InstagramImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        yield Request(item["picture"])

    def item_completed(self, results, item, info):
        result = results[0] if results else None
        if result and result[0]:
            item["picture"] = result[1]
        return item
