from urllib.parse import urlparse

from hh_parser.loaders import HhEmployerLoader
from hh_parser.spiders.hh_vacancies import HhVacanciesSpider


class HhCompanySpider(HhVacanciesSpider):
    name = "hh_company"
    start_urls = ["https://hh.ru/employers_list?query=&areaId=113&st=employersList"]
    custom_settings = {"mongo_db_collection_name": "headhunter-companies"}

    _xpath_company_selector = '//td[contains(@class, "b-companylist")][1]//a/@href'

    _xpath_company_data_mapping = {
        "title": '//div[contains(@class, "company-header")]'
        '//span[@data-qa="company-header-title-name"]/text()',
        "website": '//a[contains(@class, "g-user-content")][@data-qa="sidebar-company-site"]/@href',
        "description": '//div[contains(@class, "company-description")][@data-qa="company-description-text"]/*//text()',
        "interests": '//div[contains(@class, "bloko-text-emphasis")][contains(text(), "Сферы деятельности")]'
        "/following-sibling::p/text()",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, response, *args, **kwargs):
        yield from self.parse_companies(response)
        yield from self._follow_pagination(response, self.parse_companies)

    def parse_companies(self, response, *args, **kwargs):
        yield from self._follow_links(response, self._xpath_company_selector, self.parse_company)

    def parse_company(self, response, *args, **kwargs):
        loader = HhEmployerLoader(response=response)
        loader.add_value("company_id", urlparse(response.url).path.split("/").pop())
        loader.add_value("url", response.urljoin(response.url))
        for field_name, xpath in self._xpath_company_data_mapping.items():
            loader.add_xpath(field_name, xpath)
        yield loader.load_item()
