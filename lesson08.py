import os

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from dotenv import load_dotenv
from igraph import Graph, plot

from instagram_handshake_parser.spiders.instagram_handshake import InstagramHandshakeSpider

if __name__ == "__main__":
    graph = Graph()
    load_dotenv()
    crawler_settings = Settings()
    crawler_settings.setmodule("instagram_handshake_parser.settings")
    source_user, target_user = crawler_settings.get("INSTAGRAM_USERS")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(
        InstagramHandshakeSpider,
        users=[source_user, target_user],
        credentials={
            "username": os.getenv("INSTAGRAM_USERNAME"),
            "enc_password": os.getenv("INSTAGRAM_ENC_PASSWORD"),
        },
        max_travel_depth=crawler_settings.get("MAX_TRAVEL_DEPTH"),
        max_paths=crawler_settings.get("MAX_PATHS"),
        json_request_delay=crawler_settings.get("JSON_REQUEST_DELAY"),
        graph=graph,
    )
    crawler_proc.start()
    try:
        paths = graph.get_shortest_paths(source_user, target_user)
        shortest_path = sorted(paths, key=lambda path: len(path))[0]
        print("The shortest path is:", [graph.vs["name"][i] for i in shortest_path])
    except (AttributeError, ValueError):
        print(f"The user {source_user} does not have a connection to {target_user}")
