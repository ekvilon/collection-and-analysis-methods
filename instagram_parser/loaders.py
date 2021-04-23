from datetime import datetime

from itemloaders import ItemLoader
from itemloaders.processors import TakeFirst


class BaseInstagramLoader(ItemLoader):
    def __init__(self, **context):
        super().__init__(**context)
        self.add_value("data_parse", datetime.now())


class InstagramTagLoader(BaseInstagramLoader):
    id_out = TakeFirst()
    name_out = TakeFirst()
    picture_out = TakeFirst()
    date_parse_out = TakeFirst()


class InstagramPostLoader(BaseInstagramLoader):
    id_out = TakeFirst()
    shortcode_out = TakeFirst()
    picture_out = TakeFirst()
    date_parse_out = TakeFirst()
    data_out = TakeFirst()
