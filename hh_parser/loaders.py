from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose


def concat_strings_list(strings, separator=""):
    return separator.join(strings).replace("\xa0", " ") if strings else ""


def concat_lines_list(lines):
    return concat_strings_list(lines, "\n")


class HhVacancyLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_out = TakeFirst()
    salary_in = Compose(concat_strings_list)
    salary_out = TakeFirst()
    description_in = Compose(concat_lines_list)
    description_out = TakeFirst()
    company_id_out = TakeFirst()
    company_url_out = TakeFirst()


class HhEmployerLoader(ItemLoader):
    default_item_class = dict
    company_id_out = TakeFirst()
    url_out = TakeFirst()
    title_in = Compose(concat_strings_list)
    title_out = TakeFirst()
    website_out = TakeFirst()
    description_in = Compose(concat_lines_list)
    description_out = TakeFirst()
    interests_out = TakeFirst()
