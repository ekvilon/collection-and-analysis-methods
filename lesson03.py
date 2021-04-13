from datetime import datetime

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import get as fetch_page
from time import sleep
from urllib.parse import urlparse, urlunparse, urljoin

from database.database import Database


class Storage:
    def __init__(self, database_url):
        self._database = Database(database_url)

    def persist_post(self, post):
        self._database.create_post(post)


class GbBlogParser:
    def __init__(self, url: str, storage: Storage):
        self._url = url
        self._storage = storage

    async def _fetch_document(
        self, url, max_tries: int = 5, delay: float = 1.0, as_json: bool = False
    ):
        async with aiohttp.ClientSession() as session:
            for _ in range(max_tries):
                async with session.get(url) as response:
                    if response.status == 200:
                        if as_json:
                            return await response.json()
                        else:
                            return await response.text()
                    await asyncio.sleep(delay)
            raise Exception(
                f"{'Json document' if as_json else 'Page'} has not been fetched properly"
            )

    def _get_task(self, source):
        async def task():
            soup = (
                source
                if isinstance(source, BeautifulSoup)
                else self._get_soup(await self._fetch_document(source))
            )
            await self._parse_post_list(soup)

        return task

    async def _parse_post_list(self, soup):
        posts = soup.find_all("div", {"class": "post-item"})
        for element in posts:
            url = urljoin(self._url, element.find("a").attrs.get("href", ""))
            try:
                post = await self._parse_post(url)
            except Exception as ex:
                print(ex)
            else:
                self._storage.persist_post(post)

    async def _parse_post(self, url):
        soup = self._get_soup(await self._fetch_document(url))
        author_element = soup.find("div", {"itemprop": "author"})
        post_id = soup.find("comments").attrs.get("commentable-id")
        comments = await self._fetch_document(
            urljoin(
                self._url,
                f"/api/v2/comments?commentable_type=Post&commentable_id={post_id}&order=desc",
            ),
            as_json=True,
        )
        tag_element = soup.find("i", {"class": "i-tag"})

        data = {
            "post": {
                "title": soup.find("h1", {"class": "blogpost-title"}).text,
                "url": url,
                "id": post_id,
                "image_url": soup.find("meta", {"property": "og:image"}).attrs.get("content", ""),
                "published_at": datetime.fromisoformat(
                    soup.find("meta", {"name": "mediator_published_time"}).attrs.get("content", "")
                ),
            },
            "author": {
                "url": urljoin(url, author_element.parent.attrs.get("href", "")),
                "name": author_element.text,
            },
            "tags": [
                {"name": element.text, "url": urljoin(url, element.attrs.get("href", ""))}
                for element in tag_element.find_next_siblings("a", {"class": "small"})
            ]
            if tag_element
            else [],
            "comments": list(map(self._convert_comment_to_data, comments)),
        }
        return data

    async def get_tasks(self):
        pages_to_parse = []
        first_page = self._get_soup(await self._fetch_document(self._url))
        last_page_link = (
            first_page.find("ul", {"class": "gb__pagination"})
            .find("li", {"class": "gap"})
            .next_sibling.find("a")
        )
        count = int(last_page_link.text)
        pages_to_parse.append(first_page)
        pages_to_parse.extend(
            self._update_query(
                urljoin(self._url, last_page_link.attrs.get("href", "")), f"page={page}"
            )
            for page in range(2, count + 1)
        )
        return [asyncio.ensure_future(self._get_task(page)()) for page in pages_to_parse]

    @staticmethod
    def _get_soup(text):
        return BeautifulSoup(text, "lxml")

    @classmethod
    def _convert_comment_to_data(cls, item):
        comment = item.get("comment", {})
        user = comment.get("user", {})
        data = {
            "id": int(comment.get("id", 0)),
            "comment": {
                "parent_id": int(comment.get("parent_id", 0) or 0),
                "likes_count": int(comment.get("likes_count", 0)),
                "body": comment.get("body", ""),
                "created_at": datetime.fromisoformat(comment.get("created_at", "")),
            },
            "author": {"name": user.get("full_name", ""), "url": user.get("url", "")},
            "children": list(map(cls._convert_comment_to_data, comment.get("children", []))),
        }
        return data

    @staticmethod
    def _update_query(url, query):
        proto, host, path, params, _, fragment = urlparse(url)
        return urlunparse((proto, host, path, params, query, fragment))


async def main():
    parser = GbBlogParser("https://gb.ru/posts", Storage("sqlite:///gb_blog.db"))
    await asyncio.wait([task for task in await parser.get_tasks()])


if __name__ == "__main__":
    asyncio.run(main())
