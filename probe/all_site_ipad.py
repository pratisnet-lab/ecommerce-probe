"""Bounded 13-store Apple iPad discovery pilot; never claim success without data."""
import json
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from probe.connectivity import AGENT, check
from probe.sites.catalog import SITES

# Independently discovered public category URLs. Others start at homepage and
# look for a relevant category link; missing links are reported, not fabricated.
SEEDS = {
    "trendyol": "https://www.trendyol.com/apple-tablet-x-b101470-c103665",
    "n11": "https://www.n11.com/bilgisayar/ipad-ve-tablet?m=Apple",
    "vatan": "https://www.vatanbilgisayar.com/apple-tabletler/",
    "teknosa": "https://www.teknosa.com/apple-bilgisayar-tablet-bc-116",
}
MAX_HTML = 2_000_000

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []
    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text)))
            self._href = None
            self._text = []

def same_site(site, url):
    host = urlparse(url).hostname
    expected = urlparse(SITES[site]).hostname
    return bool(host and (host == expected or host.endswith("." + expected)))

def load_html(site, url):
    if not url.startswith("https://") or not same_site(site, url):
        return None, "invalid_url"
    robot = RobotFileParser()
    robot.set_url(f"https://{urlparse(url).hostname}/robots.txt")
    try:
        robot.read()
        if not robot.can_fetch(AGENT, url):
            return None, "robots_blocked_or_unknown"
        with urlopen(Request(url, headers={"User-Agent": AGENT, "Accept": "text/html"}), timeout=10) as response:
            if not same_site(site, response.url):
                return None, "redirect_outside_site"
            if "text/html" not in response.headers.get("Content-Type", ""):
                return None, "non_html"
            html = response.read(MAX_HTML + 1)
            if len(html) > MAX_HTML:
                return None, "too_large"
            return (html.decode("utf-8", "replace"), response.url), "html_accessible"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"

def links_for(site, html, page_url):
    parser = Anchors()
    parser.feed(html)
    found = []
    seen = set()
    for href, label in parser.links:
        url = urljoin(page_url, href).split("#", 1)[0]
        if urlparse(url).scheme != "https" or not same_site(site, url) or url in seen:
            continue
        seen.add(url)
        found.append((url, label))
    return found

def choose_categories(links, limit=2):
    return [url for url, label in links
            if ("ipad" in (url + " " + label).lower() or
                ("apple" in (url + " " + label).lower() and
                 "tablet" in (url + " " + label).lower()))][:limit]

def choose_products(links, limit=3):
    products = []
    for url, label in links:
        path = urlparse(url).path.lower()
        title = (path + " " + label.lower())
        if "ipad" not in title:
            continue
        # Reject broad categories; actual product validity is checked by JSON-LD.
        if not ("/p-" in path or "-p-" in path or "/urun/" in path
                or "/product/" in path or "/p/" in path or
                path.endswith(".html") or path.endswith(".htm")):
            continue
        products.append(url)
        if len(products) == limit:
            break
    return products

def pilot_site(site, delay=1.0):
    seed = SEEDS.get(site, SITES[site])
    first, status = load_html(site, seed)
    result = {"seed": seed, "seed_status": status, "categories": [],
              "candidate_urls": [], "checks": [], "status": "seed_unavailable"}
    if not first:
        return result
    html, final_url = first
    links = links_for(site, html, final_url)
    urls = choose_products(links)
    if not urls and site not in SEEDS:
        categories = choose_categories(links)
        result["categories"] = categories
        for category in categories:
            time.sleep(delay)
            page, _ = load_html(site, category)
            if page:
                urls.extend(choose_products(links_for(site, *page)))
            if urls:
                break
    # Site may expose Apple products in JSON-LD but no standard product links.
    urls = list(dict.fromkeys(urls))[:3]
    result["candidate_urls"] = urls
    if not urls:
        result["status"] = "no_product_links_discovered"
        return result
    for url in urls:
        time.sleep(delay)
        result["checks"].append(check(site, url))
    result["status"] = ("product_name_price_found" if any(
        any(p.get("title") and p.get("price") is not None and
            "ipad" in str(p.get("title")).lower() for p in c["products"])
        for c in result["checks"]) else "products_not_verified")
    return result

def main():
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(), "sites": {}}
    for site in SITES:
        report["sites"][site] = pilot_site(site)
        print(f"{site}: {report['sites'][site]['status']}", flush=True)
        time.sleep(1)
    output = Path("probe/output/all_site_ipad.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["## 13-site Apple iPad pilot", "", "| Site | Seed | Candidates | Name + price verified |",
             "|---|---|---:|---|"]
    for site, item in report["sites"].items():
        lines.append(f"| {site} | {item['seed_status']} | {len(item['candidate_urls'])} | {item['status']} |")
    summary = "\n".join(lines) + "\n"
    print(summary)
    import os
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary)

if __name__ == "__main__":
    main()
