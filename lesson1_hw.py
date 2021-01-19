import json
import time
from pathlib import Path
import requests


class ParseError(Exception):
    def __init__(self, txt):
        self.txt = txt


class Parse5ka:
    params = {
        "records_per_page": 50,
        "page": 1,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 "
                      "Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,uk;q=0.8,ru-RU;q=0.7,ru;q=0.6",
    }

    def __init__(self, start_url, result_path):
        self.start_url = start_url
        self.result_path = result_path

    def run(self):
        for product in self.parse(self.start_url):
            path = self.result_path.joinpath(f"{product['id']}.json")
            self.save(product, path)


    def parse(self, url):
        params = self.params
        while url:
            response = self.__get_response(url, params=params, headers=self.headers)
            if params:
                params = {}
            data = json.loads(response.text)
            url = data.get("next")
            for product in data.get("results"):
                yield product

    @staticmethod
    def __get_response(url, *args, **kwargs) -> requests.Response:
        while True:
            try:
                response = requests.get(url, *args, **kwargs)
                if response.status_code > 399:
                    raise ParseError(response.status_code)
                time.sleep(0.5)
                return response
            except (requests.RequestException, ParseError):
                time.sleep(0.5)
                continue

    @staticmethod
    def save(data, path: Path):
        with path.open("w", encoding="UTF-8") as file:
            json.dump(data, file, ensure_ascii=False)

    @staticmethod
    def save_to_json_file(data, file_name):
        with open(f"products/{file_name}.json", "w", encoding="UTF-8") as file:
            json.dump(data, file, ensure_ascii=False)


class ParserCatalog(Parse5ka):
    def __init__(self, start_url, category_url, result_path=None):
        super().__init__(start_url, result_path)
        self.category_url = category_url

    def get_categories(self, category_url):
        response = requests.get(category_url, headers=self.headers)
        return response.json()

    def run(self):
        for category in self.get_categories(self.category_url):
            data = {
                "name": category["parent_group_name"],
                "code": category["parent_group_code"],
                "products": [],
            }

            self.params["categories"] = category["parent_group_code"]

            for products in self.parse(self.start_url):
                data["products"].append(products["name"])
            self.save_to_json_file(data, category["parent_group_name"])


if __name__ == "__main__":
    parser = ParserCatalog(
        "https://5ka.ru/api/v2/special_offers/",
        "https://5ka.ru/api/v2/categories/"
    )
    parser.run()
