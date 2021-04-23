from urllib.parse import urlparse, urlunparse

import scrapy
import re

from avito_parser.loaders import AvitoAdvertLoader


class AvitoAdvertsSpider(scrapy.Spider):
    name = "avito_adverts"
    allowed_domains = ["avito.ru"]
    start_urls = ["https://www.avito.ru/krasnodar/kvartiry"]
    custom_settings = {"mongo_db_collection_name": "avito-adverts"}

    _xpath_advert_selector = '//div[@data-marker="item"][@data-item-id] \
                             [contains(@class, "js-catalog-item-enum")]//a[@itemprop="url"]/@href'
    _xpath_last_page_selector = (
        '//span[@data-marker="pagination-button/next"]/preceding-sibling::span[1]/@data-marker'
    )
    _xpath_parameters_selector = '//ul[contains(@class, "item-params-list")]/ \
                                 li[contains(@class, "item-params-list-item")]'
    _xpath_author_selector = '//a[contains(@class, "seller-info-shop-link")]/@href'

    _xpath_advert_data_mapping = {
        "title": '//h1[contains(@class, "title-info-title")]'
        '/span[contains(@class, "title-info-title-text")][@itemprop="name"]/text()',
        "price": '//span[contains(@class, "js-item-price")][@itemprop="price"]/@content',
        "address": '//div[@itemprop="address"]/span[contains(@class, "item-address__string")]/text()',
    }

    _re_page_number = re.compile(r"([0-9]+)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _follow_links(self, response, selector, callback, **kwargs):
        for link in response.xpath(selector):
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def _follow_pagination(self, response, callback, **kwargs):
        parsed_base_url = urlparse(response.url)
        last_page = response.xpath(self._xpath_last_page_selector).get()
        if last_page:
            number = self._re_page_number.search(last_page).group()
            if number:
                for n in range(2, int(number) + 1):
                    yield response.follow(
                        urlunparse(
                            parsed_base_url._replace(
                                query=parsed_base_url.query
                                + ("&" if parsed_base_url.query else "")
                                + f"p={n}"
                            )
                        )
                    )

    def parse(self, response, *args, **kwargs):
        yield from self.parse_adverts(response)
        yield from self._follow_pagination(response, self.parse_adverts)

    def parse_adverts(self, response, *args, **kwargs):
        yield from self._follow_links(response, self._xpath_advert_selector, self.parse_advert)

    def parse_advert(self, response, **kwargs):
        author = response.xpath(self._xpath_author_selector).get()
        loader = AvitoAdvertLoader(response=response)
        loader.add_value("url", response.url)
        loader.add_value("parameters", response.xpath(self._xpath_parameters_selector))
        if author:
            loader.add_value("author_url", response.urljoin(author))
        for field_name, xpath in self._xpath_advert_data_mapping.items():
            loader.add_xpath(field_name, xpath)
        yield loader.load_item()
