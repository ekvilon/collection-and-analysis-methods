# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from igraph import Graph

from instagram_handshake_parser.items import UserItem, MutualFollowingItem


def is_username_in_graph(username, graph):
    try:
        graph.vs.find(name=username)
        return True
    except ValueError:
        return False


class ItemPipeline:
    def process_item(self, item, spider):
        graph: Graph = spider.graph
        if isinstance(item, UserItem) and not is_username_in_graph(item["username"], graph):
            graph.add_vertex(item["username"])
        if isinstance(item, MutualFollowingItem):
            if not is_username_in_graph(item["source"], graph):
                graph.add_vertex(item["source"])
            if not is_username_in_graph(item["target"], graph):
                graph.add_vertex(item["target"])
            graph.add_edge(item["source"], item["target"])
        source, target = spider.users
        try:
            shortest_paths = graph.get_shortest_paths(source, target)

            if shortest_paths and len(shortest_paths) >= spider.max_travel_depth:
                spider.crawler.engine.close_spider(self, reason="finished")
        except ValueError:
            pass
        return item
