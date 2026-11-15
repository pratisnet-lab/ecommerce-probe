"""Conservative JSON-LD Product extraction from permitted HTML."""
import json
from html.parser import HTMLParser
from urllib.parse import urljoin

FIELDS = ("site", "title", "price", "currency", "url", "image", "brand", "ean", "mpn", "availability")


class ProductScripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.collect = False
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs = dict(attrs)
            self.collect = attrs.get("type", "").lower() == "application/ld+json"
            self.buffer = []

    def handle_data(self, data):
        if self.collect:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.collect:
            self.scripts.append("".join(self.buffer))
            self.collect = False


def walk(value):
    if isinstance(value, list):
        for item in value:
            yield from walk(item)
    elif isinstance(value, dict):
        yield value
        if "@graph" in value:
            yield from walk(value["@graph"])


def plain(value):
    if isinstance(value, dict):
        return value.get("name") or value.get("url")
    if isinstance(value, list):
        return plain(value[0]) if value else None
    return value


def extract(html, site, page_url):
    parser = ProductScripts()
    parser.feed(html)
    products = []
    for script in parser.scripts:
        try:
            data = json.loads(script)
        except (ValueError, TypeError):
            continue
        for item in walk(data):
            kinds = item.get("@type", [])
            kinds = [kinds] if isinstance(kinds, str) else kinds
            if "Product" not in kinds:
                continue
            offers = item.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if not isinstance(offers, dict):
                offers = {}
            image = plain(item.get("image"))
            url = urljoin(page_url, item.get("url") or page_url)
            row = {
                "site": site,
                "title": item.get("name"),
                "price": offers.get("price") or offers.get("lowPrice"),
                "currency": offers.get("priceCurrency"),
                "url": url,
                "image": urljoin(page_url, image) if isinstance(image, str) else None,
                "brand": plain(item.get("brand")),
                "ean": item.get("gtin13") or item.get("gtin") or item.get("gtin14") or item.get("gtin12") or item.get("gtin8"),
                "mpn": item.get("mpn"),
                "availability": plain(offers.get("availability")),
            }
            products.append(row)
    return products
