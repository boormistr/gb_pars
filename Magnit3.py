import bs4
from urllib.parse import urljoin
import requests
import datetime as dt
import pymongo
import os
from dotenv import load_dotenv

MONTHS = {
    "янв": 1,
    "фев": 2,
    "мар": 3,
    "апр": 4,
    "май": 5,
    "мая": 5,
    "июн": 6,
    "июл": 7,
    "авг": 8,
    "сен": 9,
    "окт": 10,
    "ноя": 11,
    "дек": 12}


class MagnitParser:

    def __init__(self, start_url, data_base):
        self.start_url = start_url
        self.database = data_base["gb_parse_02_02_2021"]

    @staticmethod
    def __get_response(url, *args, **kwargs):
        response = requests.get(url, *args, **kwargs)
        return response

    def data_template(self, dates):
        return {
            "url": lambda soups: urljoin(self.start_url, soups.attrs.get("href")),
            "promo_name": lambda soups: soups.find(
                "div", attrs={"class": "card-sale__header"}
            ).text,
            "product_name": lambda soups: str(
                soups.find("div", attrs={"class": "card-sale__title"}).text
            ),
            "old_price": lambda soups: float(
                ".".join(
                    itm
                    for itm in soups.find(
                        "div", attrs={"class": "label__price_old"}
                    ).text.split()
                )
            ),
            "new_price": lambda soups: float(
                ".".join(
                    itm
                    for itm in soups.find(
                        "div", attrs={"class": "label__price_new"}
                    ).text.split()
                )
            ),
            "image_url": lambda soups: urljoin(
                self.start_url, soups.find("img").attrs.get("data-src")
            ),
            "date_from": lambda _: next(dates),
            "date_to": lambda _: next(dates),
        }

    @staticmethod
    def date_parse(date_string: str):
        date_list = date_string.replace("с ", "", 1).replace("\n", "").split("до")
        for date in date_list:
            temp_date = date.split()
            yield dt.datetime(
                year=dt.datetime.now().year,
                day=int(temp_date[0]),
                month=MONTHS[temp_date[1][:3]],
            )

    @staticmethod
    def __get_soup(response):
        return bs4.BeautifulSoup(response.text, "lxml")

    def run(self):
        for product in self.parse(self.start_url):
            self.save(product)

    def parse(self, url):
        soup = self.__get_soup(self.__get_response(url))
        catalog_main = soup.find('div', attrs={'class': "сatalogue__main"})
        for product_tag in catalog_main.find_all('a', attrs = {'class': "card-sale"}, reversive=False):
            yield self.__get_product_data(product_tag)

    def __get_product_data(self, product_tag):
        data = {}
        try:
            dt_parser = self.date_parse(product_tag.find("div", attrs={"class": "card-sale__date"}).text)
        except AttributeError:
            dt_parser = None
        for key, pattern in self.data_template(dt_parser).items():
            try:
                data[key] = pattern(product_tag)
            except (AttributeError, TypeError):
                data[key] = None
        return data

    def save(self, data):
        collection = self.database["magnit_product"]
        collection.insert_one(data)
        print(data)


if __name__ == '__main__':
    load_dotenv('env')
    data_base = pymongo.MongoClient(os.getenv("DATA_BASE_URL"))
    parser = MagnitParser("https://magnit.ru/promo/?geo=sankt-peterbur", data_base)
    parser.run()

