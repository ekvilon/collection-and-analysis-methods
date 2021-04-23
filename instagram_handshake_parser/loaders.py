from itemloaders import ItemLoader
from itemloaders.processors import TakeFirst


class UserLoader(ItemLoader):
    username_out = TakeFirst()


class MutualFollowingLoader(ItemLoader):
    source_out = TakeFirst()
    target_out = TakeFirst()
