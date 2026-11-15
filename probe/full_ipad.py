"""Category-first Apple iPad crawl across all configured storefronts.

No product-count limit. Safety budgets limit requests/pages/time; incomplete
crawls are explicitly marked and never represented as exhaustive.
"""
import argparse
import json
import os
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from probe.all_site_ipad import SEEDS, links_for, load_html, same_site
from probe.sites.catalog import SITES
from probe.sites.extract import extract

CATEGORY_WORDS = ("tablet", "ipad", "tablets")
NEXT_WORDS = ("next", "sonraki", "ileri", "devam", "›", "»")
PRODUCT_PATHS = ("/p-", "-p-", "/urun/", "/product/", "/p/", "/dp/", ".html", ".htm")

def ipad(text):
    return "ipad" in str(text).casefold()

def category_link(url, label):
    value = (url + " " + label).casefold()
    return any(w in value for w in CATEGORY_WORDS) and not product_link(url, label)

def product_link(url, label):
    path = urlparse(url).path.casefold()
    return ipad(path + " " + label) and any(token in path for token in PRODUCT_PATHS)

def pagination_link(url, label, current):
    if url == current:
        return False
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if any(key.lower() in ("page", "sayfa", "p", "pg", "pageindex") for key in query):
        return True
    text = label.strip().casefold()
    return (text.isdigit() or any(word in text for word in NEXT_WORDS)) and parsed.path == urlparse(current).path

def crawl_site(site, max_pages=80, max_requests=300, delay=1.0):
    seed = SEEDS.get(site, SITES[site])
    result = {
        "site": site, "seed": seed, "categories": [], "category_pages": 0,
        "product_urls": [], "products": [], "errors": [], "requests": 0,
        "status": "not_started", "complete": False,
    }
    queue = deque([(seed, "category" if site in SEEDS else "home")])
    visited = set()
    product_urls = set()
    categories = set()
    records = {}
    while queue and result["requests"] < max_requests:
        url, kind = queue.popleft()
        if url in visited or not same_site(site, url):
            continue
        if kind != "product" and result["category_pages"] >= max_pages:
            result["errors"].append("category_page_budget_exhausted")
            break
        visited.add(url)
        if result["requests"]:
            time.sleep(delay)
        result["requests"] += 1
        page, status = load_html(site, url)
        if page is None:
            result["errors"].append({"url": url, "status": status})
            continue
        html, final_url = page
        if kind == "product":
            for item in extract(html, site, final_url):
                if ipad(item.get("title")) and item.get("title"):
                    records[item.get("url") or final_url] = item
            continue
        result["category_pages"] += 1
        if kind == "category":
            categories.add(url)
        links = links_for(site, html, final_url)
        # Extract embedded structured product data, when present on listing pages.
        if kind == "category":
            for item in extract(html, site, final_url):
                if ipad(item.get("title")) and item.get("title"):
                    records[item.get("url") or final_url] = item
        for target, label in links:
            if product_link(target, label):
                product_urls.add(target)
            elif kind == "category" and pagination_link(target, label, final_url):
                if target not in visited:
                    queue.append((target, "category"))
            elif category_link(target, label):
                if target not in visited and kind in ("home", "category"):
                    queue.append((target, "category"))
        # Once a product is discovered, enqueue it for detail extraction.
        pending = {u for u, k in queue if k == "product"}
        for target in sorted(product_urls - visited - pending):
            queue.append((target, "product"))
    result["categories"] = sorted(categories)
    result["product_urls"] = sorted(product_urls)
    result["products"] = list(records.values())
    remaining = [u for u, _ in queue if u not in visited]
    result["complete"] = bool(categories) and bool(result["products"]) and not remaining and not result["errors"]
    if not categories:
        result["status"] = "category_not_verified"
    elif not result["products"]:
        result["status"] = "no_ipad_details_extracted"
    elif not result["complete"]:
        result["status"] = "partial_products"
    else:
        result["status"] = "completed"
    if remaining:
        result["errors"].append(f"request_or_page_budget_remaining={len(remaining)}")
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=80)
    parser.add_argument("--max-requests", type=int, default=300)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--site", choices=list(SITES))
    args = parser.parse_args()
    if args.max_pages < 1 or args.max_requests < 1 or args.delay < 0.5:
        parser.error("Invalid crawl safety budgets")
    sites = [args.site] if args.site else list(SITES)
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(), "sites": {}}
    for site in sites:
        report["sites"][site] = crawl_site(site, args.max_pages, args.max_requests, args.delay)
        item = report["sites"][site]
        print(f"{site}: {item['status']} categories={len(item['categories'])} products={len(item['products'])}", flush=True)
    output = Path("probe/output/full_ipad.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["## Apple iPad category crawl", "",
             "| Site | Category pages | Candidate URLs | Products | Complete | Status |",
             "|---|---:|---:|---:|---|---|"]
    for site, item in report["sites"].items():
        lines.append(f"| {site} | {item['category_pages']} | {len(item['product_urls'])} | {len(item['products'])} | {item['complete']} | {item['status']} |")
    summary = "\n".join(lines) + "\n"
    print(summary)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(summary)

if __name__ == "__main__":
    main()
