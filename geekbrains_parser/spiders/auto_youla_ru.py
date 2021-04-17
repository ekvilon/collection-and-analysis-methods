import base64

import scrapy
import re

from urllib.parse import urljoin


class AutoYoulaRuSpider(scrapy.Spider):
    name = "auto_youla_ru"
    base_url = "https://youla.ru"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]

    _css_brand_selector = 'a[data-target="brand"]'
    _css_pagination_button_selector = 'a[data-target-id="button-link-serp-paginator"]'
    _css_advertisement_title_selector = 'a[data-target="serp-snippet-title"]'

    _re_site_id = re.compile(r"%22youlaId%22%2C%22([a-z0-9]+)%22", re.IGNORECASE)
    _re_phone = re.compile(r"%22phone%22%2C%22([a-z0-9]+)%3D%3D%22", re.IGNORECASE)

    def __init__(self, persistor, *args, **kwargs):
        self._persistor = persistor
        super().__init__(*args, **kwargs)

    @classmethod
    def get_contact_data(cls, response):
        expression = "window.transitState = decodeURIComponent"

        for script in response.css("script"):
            try:
                if expression in script.css("::text").get():
                    site_id = script.re_first(cls._re_site_id)
                    phone = script.re_first(cls._re_phone)

                    result = {
                        "site_id": site_id or "",
                        "phone": cls.decode_phone(phone + "==") if phone else "",
                    }

                    return result
            except TypeError:
                pass

    @staticmethod
    def decode_phone(phone: str):
        try:
            processed = base64.decodebytes(phone.encode("ascii")).decode("ascii")
            return base64.decodebytes(processed.split("_")[0].encode("ascii")).decode("ascii")
        except ValueError:
            return ""

    def _follow_links(self, response, selector, callback, **kwargs):
        for a in response.css(selector):
            link = a.attrib.get("href")
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def parse(self, response, *args, **kwargs):
        yield from self._follow_links(response, self._css_brand_selector, self.parse_brand)

    def parse_brand(self, response, **kwargs):
        yield from self._follow_links(
            response, self._css_pagination_button_selector, self.parse_brand
        )
        yield from self._follow_links(
            response, self._css_advertisement_title_selector, self.parse_advertisement
        )

    def parse_advertisement(self, response):
        contact_data = self.get_contact_data(response)

        data = {
            "title": response.css('div[data-target="advert-title"]::text').get(),
            "photos": [
                image.attrib.get("src", "")
                for image in response.css("figure.PhotoGallery_photo__36e_r img")
            ],
            "characteristics": [
                {
                    "name": row.css(".AdvertSpecs_label__2JHnS::text").get(),
                    "value": row.css(".AdvertSpecs_data__xK2Qx::text").get()
                    or row.css(".AdvertSpecs_data__xK2Qx a::text").get(),
                }
                for row in response.css("div.AdvertCard_specs__2FEHc .AdvertSpecs_row__ljPcX")
            ],
            "descriptions": response.css(".AdvertCard_descriptionInner__KnuRi::text").get(),
            "price": float(
                response.css("div.AdvertCard_price__3dDCr::text").get().replace("\u2009", "")
            ),
            "author": {
                # todo: add support of making url for car sealer
                "url": urljoin(self.base_url, f"/user/{contact_data.get('site_id')}"),
                "phone": contact_data["phone"],
            },
        }
        self._persistor.persist(data)
