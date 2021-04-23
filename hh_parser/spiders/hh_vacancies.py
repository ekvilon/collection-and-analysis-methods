from urllib.parse import urlparse

import scrapy
import re

from hh_parser.loaders import HhVacancyLoader


class HhVacanciesSpider(scrapy.Spider):
    name = "hh_vacancies"
    base_url = "https://hh.ru"
    allowed_domains = ["hh.ru"]
    start_urls = ["https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113"]
    custom_settings = {"mongo_db_collection_name": "headhunter-vacancies"}

    _xpath_vacancy_selector = '//a[@data-qa="vacancy-serp__vacancy-title"]/@href'
    _xpath_last_page_selector = (
        '//div[@data-qa="pager-block"]/'
        'span[contains(@class, "pager-item-not-in-short-range")]'
        '//a[contains(@class, "bloko-button")]/@href'
    )
    _xpath_employer_url_selector = '//a[@data-qa="vacancy-company-name"]/@href'

    _xpath_vacancy_data_mapping = {
        "title": '//h1[@data-qa="vacancy-title"]//text()',
        "salary": '//p[contains(@class, "vacancy-salary")]//span[contains(@class, "bloko-header-2")]/text()',
        "description": '//div[contains(@class, "g-user-content")][@data-qa="vacancy-description"]/*//text()',
        "skills": '//div[contains(@class, "bloko-tag")][contains(@data-qa, "skills-element")]'
        '//span[contains(@class, "bloko-tag__section_text")]/text()',
    }

    _re_page_number = re.compile(r"(?<=page=)[0-9]+")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _follow_links(self, response, selector, callback, **kwargs):
        for link in response.xpath(selector):
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def _follow_pagination(self, response, callback, **kwargs):
        last_page = response.xpath(self._xpath_last_page_selector).get()
        if last_page:
            number = self._re_page_number.search(last_page).group()
            if number:
                for n in range(1, int(number) + 1):
                    yield response.follow(
                        response.urljoin(self._re_page_number.sub(str(n), last_page))
                    )

    def parse(self, response, *args, **kwargs):
        yield from self.parse_vacancies(response)
        yield from self._follow_pagination(response, self.parse_vacancies)

    def parse_vacancies(self, response, *args, **kwargs):
        yield from self._follow_links(response, self._xpath_vacancy_selector, self.parse_vacancy)

    def parse_vacancy(self, response, **kwargs):
        company_url = response.xpath(self._xpath_employer_url_selector).get()
        company_id = urlparse(company_url).path.split("/").pop()
        loader = HhVacancyLoader(response=response)
        loader.add_value("url", response.url)
        loader.add_value("company_url", response.urljoin(company_url))
        loader.add_value("company_id", company_id)
        for field_name, xpath in self._xpath_vacancy_data_mapping.items():
            loader.add_xpath(field_name, xpath)
        yield loader.load_item()
