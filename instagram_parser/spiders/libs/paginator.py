import json
from itertools import count
from urllib.parse import urlencode


class InstagramTagPaginator:
    query_hash = "9b498c08113f1e09617a1703c22b2f32"
    page = count(1)

    def __init__(self, tag_name):
        self.variables = {"tag_name": tag_name}

    def get_query(self, first: int = 1, end_cursor: str = None):
        self.variables["first"] = first
        if end_cursor:
            self.variables["after"] = end_cursor
        return urlencode({"query_hash": self.query_hash, "variables": json.dumps(self.variables)})
