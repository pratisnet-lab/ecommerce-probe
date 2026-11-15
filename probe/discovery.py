"""Discover iPad product candidates from publicly accessible store category pages."""
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from probe.sites.catalog import SITES

# Category entry points must be verified individually; never invent product URLs.
CATEGORY_URLS = {
    "teknosa": "https://www.teknosa.com/apple-bilgisayar-tablet-bc-116",
}

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)
            if attrs.get("href"):
                self.links.append((attrs["href"], attrs.get("title", "")))

def candidates(site, html, category_url, limit=3):
    parsed = Links()
    parsed.feed(html)
    expected = urlparse(SITES[site]).hostname
    found = []
    seen = set()
    for href, title in parsed.links:
        url = urljoin(category_url, href).split("#", 1)[0]
        parts = urlparse(url)
        if parts.scheme != "https" or parts.hostname != expected:
            continue
        if "ipad" not in (parts.path + " " + title).lower():
            continue
        if not parts.path or url in seen:
            continue
        # Product-looking paths only; category and campaign pages are not products.
        if not ("/p-" in parts.path or "-p-" in parts.path):
            continue
        seen.add(url)
        found.append(url)
        if len(found) >= limit:
            break
    return found
