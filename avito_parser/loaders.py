import re

from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose


re_whitespaces = re.compile(r"\xa0|^\s+|\s+$")
re_empty_value = re.compile(r"^\s+$")


def remove_whitespaces(string):
    return re_whitespaces.sub("", string) if string else ""


def convert_parameters_to_dict(elements):
    result = {}
    for element in elements:
        try:
            label, value = list(
                filter(
                    lambda item: not re_empty_value.findall(item),
                    element.xpath(
                        'span[contains(@class, "item-params-label")]/text() | text() | */text()'
                    ).getall(),
                )
            )

            result.setdefault(label.split(":")[0], re_whitespaces.sub("", value))
        except (ValueError, AttributeError):
            pass
    return result


class AvitoAdvertLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_in = MapCompose(remove_whitespaces)
    title_out = TakeFirst()
    price_in = MapCompose(float)
    price_out = TakeFirst()
    address_in = MapCompose(remove_whitespaces)
    address_out = TakeFirst()
    parameters_in = Compose(convert_parameters_to_dict)
    parameters_out = TakeFirst()
    author_url_out = TakeFirst()
