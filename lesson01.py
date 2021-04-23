import json
import time
from pathlib import Path
from requests import get, Response


class CategoriesParser5ka:
    def __init__(self, categories_url: str, products_url: str, output_path: Path):
        self._categories_url = categories_url
        self._products_url = products_url
        self._output_path = output_path

    @staticmethod
    def _fetch(url, max_tries: int = 5, delay: float = 1.0) -> Response:
        tries = 0
        while True:
            response = get(url, headers={"User-Agent": "Not google"})
            if response.status_code == 200:
                return response
            time.sleep(delay)
            tries += 1
            if tries > max_tries:
                break

    @staticmethod
    def _save(data: dict, file_path: Path):
        file_path.write_text(json.dumps(data, ensure_ascii=False))

    def _fetch_categories(self):
        response = self._fetch(self._categories_url)
        return response.json()

    def _fetch_products(self, params: str):
        url = f"{self._products_url}{params}"
        while url:
            response = self._fetch(url)
            data = response.json()
            url = data["next"]
            for product in data.get("results", []):
                yield product

    def run(self):
        for category in self._fetch_categories():
            data = {
                "name": category["name"],
                "code": category["parent_group_code"],
                "products": [],
            }
            params = f"?categories={data['code']}"
            data["products"].extend(list(self._fetch_products(params)))
            self._save(data, self._output_path.joinpath(f"{data['code']}.json"))


if __name__ == "__main__":
    parser = CategoriesParser5ka(
        categories_url="https://5ka.ru/api/v2/categories/",
        products_url="https://5ka.ru/api/v2/special_offers/",
        output_path=Path(".") / "categories",
    )
    parser.run()
