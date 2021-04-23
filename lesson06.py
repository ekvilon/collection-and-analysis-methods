from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from avito_parser.spiders.avito_adverts import AvitoAdvertsSpider

if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule("avito_parser.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(AvitoAdvertsSpider)
    crawler_proc.start()
