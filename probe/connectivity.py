"""Small, rate-limited connectivity smoke test; not proof of product extraction."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from probe.sites.catalog import SITES
from probe.sites.extract import extract

AGENT = "EcommerceProbe/0.1 (+research; respects robots.txt)"
MAX_BYTES = 2_000_000


def check(site, url, timeout=10):
    expected = urlparse(SITES[site]).hostname
    parsed = urlparse(url)
    result = {"site": site, "url": url, "http_status": None, "status": "not_tested",
              "products": [], "error": None}
    if parsed.scheme != "https" or not parsed.hostname or (
        parsed.hostname != expected and not parsed.hostname.endswith("." + expected)
    ):
        result.update(status="invalid_url", error="URL outside allowed storefront")
        return result
    try:
        robot = RobotFileParser()
        robot.set_url(f"https://{parsed.hostname}/robots.txt")
        robot.read()
        if not robot.can_fetch(AGENT, url):
            result["status"] = "robots_blocked_or_unknown"
            return result
        request = Request(url, headers={"User-Agent": AGENT, "Accept": "text/html"})
        with urlopen(request, timeout=timeout) as response:
            result["http_status"] = response.status
            final_host = urlparse(response.url).hostname
            if final_host != expected and not final_host.endswith("." + expected):
                result.update(status="redirect_outside_site", error="Redirect left storefront")
                return result
            if "text/html" not in response.headers.get("Content-Type", ""):
                result["status"] = "non_html"
                return result
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                result["status"] = "too_large"
                return result
            products = extract(data.decode("utf-8", errors="replace"), site, response.url)
            result["products"] = products[:3]
            result["status"] = "products_found" if result["products"] else "html_accessible_no_product"
    except HTTPError as exc:
        result.update(status="http_error", http_status=exc.code, error=str(exc))
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        result.update(status="connection_error", error=f"{type(exc).__name__}: {exc}")
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", default="probe/targets.json")
    parser.add_argument("--output", default="probe/output/connectivity.json")
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()
    if args.delay < 0.5:
        parser.error("Minimum delay is 0.5 seconds")
    targets = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    if not isinstance(targets, dict) or any(
        k not in SITES or not isinstance(v, list) or any(not isinstance(u, str) for u in v)
        for k, v in targets.items()
    ):
        parser.error("Invalid target configuration")
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(), "sites": {}}
    for site, homepage in SITES.items():
        urls = targets.get(site, [])[:3]
        # A homepage tests connectivity, not product extraction.
        checks = [check(site, homepage)]
        for url in urls:
            time.sleep(args.delay)
            checks.append(check(site, url))
        report["sites"][site] = checks
        time.sleep(args.delay)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
