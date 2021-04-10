from bs4 import BeautifulSoup
from bs4.element import Tag
from dateparser import parse as parse_date
from datetime import datetime
from pymongo import MongoClient
from regex import regex
from requests import get as fetch_page
from time import sleep
from urllib.parse import urljoin


class Storage:
    def __init__(self, database_url, database_name: str, collection_name: str):
        self._db = MongoClient(database_url).get_database(database_name)
        self._collection = self._db.get_collection(collection_name)

    def save(self, document, id_property, id_value):
        record = self._collection.find_one({id_property: id_value})
        if record is None:
            self._collection.insert_one(document)
        else:
            self._collection.update_one({id_property: id_value}, {"$set": document})


class MagnitParser:
    _date_strip_re = regex.compile(r"^(с|до)\s+")

    def __init__(self, url, storage: Storage):
        self._url = url
        self._storage = storage

    def _fetch_page(self, max_tries: int = 5, delay: float = 1.0):
        for _ in range(max_tries):
            response = fetch_page(self._url)
            if response.status_code == 200:
                return response.text
            sleep(delay)
        raise Exception("Page has not been fetched properly")

    def _parse_page(self, soup: BeautifulSoup):
        return list(soup.find_all("a", {"class": "card-sale"}))

    def _parse_product(self, element: Tag):
        return {
            "url": urljoin(self._url, element.attrs.get("href", "")),
            "promo_name": element.find("div", {"class": "card-sale__header"}).text.strip(),
            "product_name": element.find("div", {"class": "card-sale__title"}).text.strip(),
            "old_price": float(
                ".".join(
                    part
                    for part in element.find("div", {"class": "label__price_old"}).text.split()
                )
            ),
            "new_price": float(
                ".".join(
                    part
                    for part in element.find("div", {"class": "label__price_new"}).text.split()
                )
            ),
            "image_url": urljoin(self._url, element.find("img").attrs.get("data-src", "")),
            "date_from": self._get_date(
                element.find("div", {"class": "card-sale__date"}).find_all("p")[0].text
            ),
            "date_to": self._get_date(
                element.find("div", {"class": "card-sale__date"}).find_all("p")[1].text
            ),
        }

    def _persist_product(self, product):
        self._storage.save(product, "url", product["url"])

    def run(self):
        products = self._parse_page(self._get_soup(self._fetch_page()))
        for element in products:
            try:
                product = self._parse_product(element)
            except (ValueError, AttributeError):
                pass
            self._persist_product(product)

    @classmethod
    def _get_date(cls, text: str):
        date: datetime = parse_date(cls._date_strip_re.sub("", text))
        if date.month < datetime.now().month:
            date = date.replace(year=date.year + 1)
        return date

    @staticmethod
    def _get_soup(text):
        return BeautifulSoup(text, "lxml")


if __name__ == "__main__":
    parser = MagnitParser(
        "https://magnit.ru/promo/",
        storage=Storage(
            "mongodb://localhost:27017", database_name="col-an-methods", collection_name="lesson2"
        ),
    )
    parser.run()
