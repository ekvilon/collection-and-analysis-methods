import os

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from dotenv import load_dotenv

from instagram_parser.spiders.instagram import InstagramSpider


if __name__ == "__main__":
    load_dotenv()
    crawler_settings = Settings()
    crawler_settings.setmodule("instagram_parser.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(
        InstagramSpider,
        tags=crawler_settings.get("INSTAGRAM_TAGS"),
        credentials={
            "username": os.getenv("INSTAGRAM_USERNAME"),
            "enc_password": os.getenv("INSTAGRAM_ENC_PASSWORD"),
        },
    )
    crawler_proc.start()
