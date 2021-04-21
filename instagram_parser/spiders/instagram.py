import scrapy
from scrapy import FormRequest
import json
from scrapy.http import JsonRequest

from instagram_parser.loaders import InstagramTagLoader, InstagramPostLoader
from instagram_parser.spiders.lib.paginator import InstagramTagPaginator
from instagram_parser.spiders.lib.utils import get_cookies


class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    custom_settings = {"mongo_db_collection_name": "instagram"}

    def __init__(self, tags: list, credentials: dict, **kwargs):
        self.credentials = credentials
        self.tags = tags
        super().__init__(**kwargs)

    def authenticate_on_need(self, response):
        cookies = get_cookies(response)

        if cookies.get("ds_user_id"):
            return None
        else:
            return FormRequest(
                url="https://www.instagram.com/accounts/login/ajax/",
                method="POST",
                formdata=self.credentials,
                headers={b"X-CSRFToken": cookies.get("csrftoken")},
                callback=self.parse_authentication,
                cb_kwargs={"original_response": response},
            )

    def parse_authentication(self, _, original_response):
        yield original_response.request

    def get_shared_data(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData")]/text()').get()

        try:
            return json.loads(script[21:-1])
        except ValueError as exception:
            print(exception)
            return {}

    def get_next_end_cursor(self, data):
        media_data = data["edge_hashtag_to_media"]
        page_info = media_data.get("page_info") if "page_info" in media_data else None
        if page_info and page_info.get("has_next_page"):
            return page_info.get("end_cursor")

    def get_tag_data(self, response):
        if response.headers.get(b"Content-Type").find(b"/json") == -1:
            return self.get_shared_data(response)["entry_data"]["TagPage"][0]["graphql"]["hashtag"]
        else:
            return response.json()["data"]["hashtag"]

    def parse_more_posts(self, response, tag_paginator, tag_data):
        end_cursor = self.get_next_end_cursor(tag_data)
        if end_cursor:
            yield JsonRequest(
                url=response.urljoin(
                    f"/graphql/query/?"
                    f"{tag_paginator.get_query(first=next(tag_paginator.page), end_cursor=end_cursor)}"
                ),
                callback=self.parse_posts,
                cb_kwargs={"tag_paginator": tag_paginator},
            )
        else:
            return []

    def parse(self, response, **kwargs):
        authentication = self.authenticate_on_need(response)
        if authentication:
            yield authentication
        else:
            for tag in self.tags:
                yield response.follow(f"/explore/tags/{tag}/", callback=self.parse_tag)

    def parse_tag(self, response):
        tag_data = self.get_tag_data(response)
        tag_paginator = InstagramTagPaginator(tag_data["name"])

        yield from self._process_tag(tag_data)
        yield from self._process_posts(tag_data)
        yield from self.parse_more_posts(response, tag_paginator, tag_data)

    def parse_posts(self, response, tag_paginator: InstagramTagPaginator):
        tag_data = self.get_tag_data(response)
        tag_paginator = InstagramTagPaginator(tag_data["name"])

        yield from self._process_posts(tag_data)
        yield from self.parse_more_posts(response, tag_paginator, tag_data)

    def _process_posts(self, data):
        posts = data.get("edge_hashtag_to_media")

        if posts:
            for post in posts.get("edges", []):
                try:
                    yield from self._process_post(post)
                except Exception as exception:
                    print(exception)
        return []

    def _process_tag(self, tag):
        loader = InstagramTagLoader()
        loader.add_value("id", tag["id"])
        loader.add_value("name", tag["name"])
        loader.add_value("picture", tag["profile_pic_url"])
        yield loader.load_item()

    def _process_post(self, post):
        data = post["node"]
        loader = InstagramPostLoader()
        loader.add_value("id", data["id"])
        loader.add_value("shortcode", data["shortcode"])
        loader.add_value("picture", data["display_url"])
        loader.add_value("data", data)
        yield loader.load_item()
