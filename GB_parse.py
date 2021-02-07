import os
import requests
import bs4
from urllib.parse import urljoin
from dotenv import load_dotenv
from datetime import datetime
from database import Database


class GbParse:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 "
                      "Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,uk;q=0.8,ru-RU;q=0.7,ru;q=0.6",
    }

    def __init__(self, start_url, comments_url, database):
        self.start_url = start_url
        self.comments_url = comments_url
        self.done_urls = set()
        self.tasks = [self.parse_task(self.start_url, self.pag_parse)]
        self.done_urls.add(self.start_url)
        self.database = database
        self.result_comments = []


    @staticmethod
    def _get_response(*args, **kwargs):
        return requests.get(*args, **kwargs)

    def _get_soup(self, *args, **kwargs):
        response = self._get_response(*args, **kwargs)
        soup = bs4.BeautifulSoup(response.text, "lxml")
        return soup

    def parse_task(self, url, callback):
        def wrap():
            soup = self._get_soup(url)
            return callback(url, soup)
        return wrap

    def run(self):
        for task in self.tasks:
            result = task()
            if result:
                self.database.create_post(result)

    def pag_parse(self, url, soup: bs4.BeautifulSoup):
        gb_pagination = soup.find("ul", attrs={"class": "gb__pagination"})
        a_tags = gb_pagination.find_all("a")
        for a in a_tags:
            pag_url = urljoin(url, a.get("href"))
            if pag_url not in self.done_urls:
                task = self.parse_task(pag_url, self.pag_parse)
                self.tasks.append(task)
                self.done_urls.add(pag_url)

        posts_urls = soup.find_all("a", attrs={"class": "post-item__title"})
        for post_url in posts_urls:
            post_href = urljoin(url, post_url.get("href"))
            if post_href not in self.done_urls:
                task = self.parse_task(post_href, self.post_parse)
                self.tasks.append(task)
                self.done_urls.add(post_href)

    def get_comments_info(self, comments):
        for comment in comments:
            self.result_comments.append({'id': comment['comment']['id'],
                                         'author_id': comment['comment']['user']['id'],
                                         'text': comment['comment']['body']})
            if comment['comment']['children']:
                for el in comment['comment']['children']:
                    self.get_comments_info([el])
        return self.result_comments

    def post_parse(self, url, soup: bs4.BeautifulSoup) -> dict:
        author_name_tag = soup.find("div", attrs={"itemprop": "author"})
        id_article = soup.find("div", attrs={'class': "referrals-social-buttons-small-wrapper"}).get('data-minifiable-id')
        post_comments_url = self.comments_url+id_article
        self.result_comments = []
        data = {
            "post_data": {
                "url": url,
                "title": soup.find("h1", attrs={"class": "blogpost-title"}).text,
                "pic_url": soup.find('img').get("src"),
                "date": datetime.strptime(soup.find("time").get('datetime')[:-6], "%Y-%m-%dT%H:%M:%S")
            },

            "author": {"url": urljoin(url, author_name_tag.parent.get("href")), "name": author_name_tag.text},
            "tags": [
                {
                    "name": tag.text,
                    "url": urljoin(url, tag.get("href")),
                }
                for tag in soup.find_all("a", attrs={"class": "small"})
            ],
            "comments": self.get_comments_info(requests.get(post_comments_url, headers=self.headers).json())
        }

        print(data)
        return data


if __name__ == '__main__':
    load_dotenv(".env")
    parser = GbParse("https://geekbrains.ru/posts",
                     "https://geekbrains.ru/api/v2/comments?commentable_type=Post&commentable_id=",
                     Database(os.getenv("SQLDB")))
    parser.run()
