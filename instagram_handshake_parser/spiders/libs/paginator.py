import json
from abc import ABC, abstractmethod
from itertools import count
from urllib.parse import urlencode


class BasePaginator(ABC):
    @abstractmethod
    def get_query(self, page_number: int = 1, end_cursor: str = None):
        pass


class Paginator(BasePaginator):
    query_hash = ""
    page = count(1)

    def __init__(self, **kwargs):
        self.variables = kwargs

    def get_query(self, page_number: int = 100, end_cursor: str = None):
        self.variables["first"] = page_number
        if end_cursor:
            self.variables["after"] = end_cursor
        return urlencode({"query_hash": self.query_hash, "variables": json.dumps(self.variables)})


class PaginatorFollowings(Paginator):
    query_hash = "3dec7e2c57367ef3da3d987d89f9dbc8"

    def __init__(self, **kwargs):
        args = {**kwargs, "include_reel": True, "fetch_mutual": True}
        super().__init__(**args)
