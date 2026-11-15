"""Phase 1: only verify storefront access, tablet categories and iPad links.

No product detail requests, persistence, or database writes. JSON is a test
artifact only. Discovery is best-effort; do not infer exhaustive inventory.
"""
import argparse
import json
import os
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from probe.all_site_ipad import SEEDS, links_for, load_html, same_site
from probe.sites.catalog import SITES

def is_ipad(url, label):
    text = (urlparse(url).path + " " + label).casefold()
    return "ipad" in text and any(
        marker in urlparse(url).path.casefold()
        for marker in ("/p-", "-p-", "/urun/", "/product/", "/p/", "/dp/", "-pm-", "-pd-", ".html")
    )

def is_tablet_category(url, label):
    text = (urlparse(url).path + " " + label).casefold()
    if any(x in text for x in ("aksesuar", "accessories", "blog", "yardim", "campaign", "kampanya")):
        return False
    return ("tablet" in text or "ipad" in text) and not is_ipad(url, label)

def is_next_page(url, label, current):
    if urlparse(url).path != urlparse(current).path:
        return False
    params = parse_qs(urlparse(url).query)
    if any(k.lower() in ("page", "sayfa", "pg", "pageindex") for k in params):
        return True
    return label.strip().casefold() in ("next", "sonraki", "ileri", "›", "»")

def discover(site, max_pages=60, delay=1.0):
    seed = SEEDS.get(site, SITES[site])
    queue = deque([(seed, 0, "seed")])
    seen = set()
    categories = set()
    products = set()
    failures = []
    homepage_accessible = False
    while queue and len(seen) < max_pages:
        url, depth, kind = queue.popleft()
        if url in seen or not same_site(site, url):
            continue
        seen.add(url)
        if len(seen) > 1:
            time.sleep(delay)
        page, status = load_html(site, url)
        if not page:
            failures.append({"url": url, "reason": status})
            continue
        if kind == "seed":
            homepage_accessible = True
        if kind == "category" or (kind == "seed" and site in SEEDS):
            categories.add(url)
        html, final = page
        category_count = 0
        for link, label in links_for(site, html, final):
            if is_ipad(link, label):
                products.add(link)
            elif kind != "seed" or site in SEEDS:
                if is_next_page(link, label, final) and link not in seen:
                    queue.append((link, depth, "category"))
            if is_tablet_category(link, label) and depth < 3 and category_count < 12:
                queue.append((link, depth + 1, "category"))
                category_count += 1
    truncated = bool(queue)
    return {
        "site": site, "seed": seed, "seed_accessible": homepage_accessible,
        "tablet_categories": sorted(categories), "ipad_urls": sorted(products),
        "ipad_count": len(products), "pages_checked": len(seen),
        "truncated": truncated, "failures": failures,
        "status": ("blocked_or_unreachable" if not homepage_accessible else
                   "category_not_found" if not categories else
                   "ipad_links_found" if products else "no_ipad_links_found"),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", choices=list(SITES))
    parser.add_argument("--max-pages", type=int, default=60)
    args = parser.parse_args()
    if args.max_pages < 1:
        parser.error("max-pages must be positive")
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(), "sites": {}}
    for site in ([args.site] if args.site else SITES):
        result = discover(site, max_pages=args.max_pages)
        report["sites"][site] = result
        print(f"{site}: {result['status']} categories={len(result['tablet_categories'])} ipad_links={result['ipad_count']} failures={len(result['failures'])}", flush=True)
    output = Path("probe/output/discovery_only.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["## Phase 1: access and Apple iPad discovery", "",
             "| Site | Access | Tablet categories | iPad links | Pages | Truncated | Errors |",
             "|---|---|---:|---:|---:|---|---:|"]
    for site, item in report["sites"].items():
        lines.append(f"| {site} | {item['seed_accessible']} | {len(item['tablet_categories'])} | {item['ipad_count']} | {item['pages_checked']} | {item['truncated']} | {len(item['failures'])} |")
    summary = "\n".join(lines) + "\n"
    print(summary)
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(summary)

if __name__ == "__main__":
    main()
