from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from hh_parser.spiders.hh_company import HhCompanySpider
from hh_parser.spiders.hh_vacancies import HhVacanciesSpider

if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule("hh_parser.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(HhVacanciesSpider)
    crawler_proc.crawl(HhCompanySpider)
    crawler_proc.start()
