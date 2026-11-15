"""Self-contained, tiny iPad discovery and extraction pilot."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from probe.connectivity import AGENT, check
from probe.discovery import CATEGORY_URLS, candidates
from probe.sites.catalog import SITES

def discover(site, category_url):
    expected = urlparse(SITES[site]).hostname
    result = {"site": site, "category_url": category_url, "status": "not_tested",
              "candidates": [], "error": None}
    robot = RobotFileParser()
    robot.set_url(f"https://{expected}/robots.txt")
    try:
        robot.read()
        if not robot.can_fetch(AGENT, category_url):
            result["status"] = "robots_blocked_or_unknown"
            return result
        with urlopen(Request(category_url, headers={"User-Agent": AGENT}), timeout=10) as response:
            if urlparse(response.url).hostname != expected:
                result["status"] = "redirect_outside_site"
                return result
            if "text/html" not in response.headers.get("Content-Type", ""):
                result["status"] = "non_html"
                return result
            data = response.read(2_000_001)
            if len(data) > 2_000_000:
                result["status"] = "too_large"
                return result
            result["candidates"] = candidates(site, data.decode("utf-8", "replace"), response.url)
            result["status"] = "candidates_found" if result["candidates"] else "no_candidates"
    except Exception as exc:
        result.update(status="error", error=f"{type(exc).__name__}: {exc}")
    return result

def main():
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(), "sites": {}}
    for site in SITES:
        category = CATEGORY_URLS.get(site)
        if not category:
            report["sites"][site] = {"status": "category_not_configured", "checks": []}
            continue
        discovery = discover(site, category)
        checks = []
        for url in discovery["candidates"][:3]:
            time.sleep(1)
            checks.append(check(site, url))
        report["sites"][site] = {"discovery": discovery, "checks": checks}
    output = Path("probe/output/ipad_pilot.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for site, info in report["sites"].items():
        checks = info.get("checks", [])
        verified = sum(any(p.get("title") and p.get("price") is not None
                           and "ipad" in str(p.get("title")).lower()
                           for p in c["products"]) for c in checks)
        print(f"{site}: {info.get('status', info.get('discovery', {}).get('status'))}; verified={verified}")
if __name__ == "__main__":
    main()
