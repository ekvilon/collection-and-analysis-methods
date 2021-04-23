from asyncio import sleep

import scrapy
import json
import aiohttp
from igraph import Graph
from scrapy import FormRequest
from scrapy.http import Response

from instagram_handshake_parser.items import UserItem, MutualFollowingItem
from instagram_handshake_parser.loaders import UserLoader, MutualFollowingLoader
from instagram_handshake_parser.spiders.libs.paginator import PaginatorFollowings, Paginator
from instagram_handshake_parser.spiders.libs.utils import get_cookies


class InstagramHandshakeSpider(scrapy.Spider):
    name = "instagram_handshake"
    allowed_domains = ["instagram.com"]
    start_urls = ["https://www.instagram.com/"]

    def __init__(
        self,
        users: list,
        credentials: dict,
        max_travel_depth: int,
        max_paths: int,
        json_request_delay: int,
        graph: Graph,
        **kwargs,
    ):
        self.credentials = credentials
        self.users = users
        self.max_travel_depth = max_travel_depth
        self.max_paths = max_paths
        self.json_request_delay = json_request_delay
        self.graph = graph
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

    def get_user_data(self, response):
        if response.headers.get(b"Content-Type").find(b"/json") == -1:
            shared_data = self.get_shared_data(response)
            return shared_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
        else:
            return response.json()["data"]["user"]

    async def fetch_usernames_with_graphql_api(
        self, response: Response, paginator: Paginator, edge: str
    ):
        usernames = []
        headers = {
            key.decode(): value[0].decode() for key, value in response.request.headers.items()
        }
        headers["Content-Type"] = "application/json; charset=utf-8"
        async with aiohttp.ClientSession() as session:
            fails = 0
            end_cursor = ""
            while True and fails < 3:
                query = paginator.get_query(end_cursor=end_cursor)
                async with session.get(
                    response.urljoin(f"/graphql/query/?{query}"), headers=headers
                ) as new_response:
                    try:
                        data = await new_response.json()
                        user_data = data["data"]["user"][edge]
                        page_info = user_data["page_info"]
                        edges = user_data["edges"]
                        if edges:
                            for user in edges:
                                usernames.append(user["node"]["username"])
                        if page_info["has_next_page"]:
                            end_cursor = page_info["end_cursor"]
                            fails = 0
                        else:
                            break
                        await sleep(self.json_request_delay)
                    except Exception as exception:
                        fails = fails + 1
                        print(
                            new_response.status,
                            new_response.reason,
                            new_response.content,
                            exception,
                        )
        return usernames

    def parse(self, response, **kwargs):
        authentication = self.authenticate_on_need(response)
        if authentication:
            yield authentication
        else:
            for user in self.users:
                yield response.follow(
                    f"/{user}/", callback=self.parse_user, cb_kwargs={"depth": 0}
                )

    async def parse_user(self, response, depth):
        user_data = self.get_user_data(response)

        yield self._process_user(user_data)
        mutual_followings = await self.get_mutual_followings(response, user_data["id"])

        if mutual_followings:
            for following in mutual_followings:
                yield self._process_mutual_following(user_data["username"], following)
            if depth < self.max_travel_depth:
                for following in mutual_followings:
                    yield response.follow(
                        f"/{following}/", callback=self.parse_user, cb_kwargs={"depth": depth + 1}
                    )

    async def get_mutual_followings(self, response, user_id):
        followings = await self.fetch_usernames_with_graphql_api(
            response, PaginatorFollowings(id=user_id), "edge_follow"
        )

        return followings

    def _process_user(self, user):
        loader = UserLoader(UserItem())
        loader.add_value("username", user["username"])
        return loader.load_item()

    def _process_mutual_following(self, source, target):
        loader = MutualFollowingLoader(MutualFollowingItem())
        loader.add_value("source", source)
        loader.add_value("target", target)
        return loader.load_item()
