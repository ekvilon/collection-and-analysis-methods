# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from itertools import cycle


class AvitoParserSpiderRotatingUserAgentsMiddleware:
    def __init__(self):
        pass

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        setattr(s, "userAgents", cycle(crawler.settings.get("USER_AGENTS")))
        return s

    def process_request(self, request, spider):
        request.headers[b"User-Agent"] = next(self.userAgents)
        return None
