"""Run safe, explicit URL probes. No search-engine scraping or bypasses."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from probe.sites.catalog import SITES
from probe.sites.extract import FIELDS, extract

ROOT = Path(__file__).resolve().parent
USER_AGENT = "EcommerceProbe/0.1 (+research; respects robots.txt)"


def allowed(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    robots_url = f"https://{parsed.hostname}/robots.txt"
    robot = RobotFileParser()
    try:
        robot.set_url(robots_url)
        robot.read()
        return robot.can_fetch(USER_AGENT, url)
    except Exception:
        return False


def fetch(url):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urlopen(req, timeout=12) as response:
        if urlparse(response.url).hostname != urlparse(url).hostname:
            raise ValueError("Cross-domain redirect blocked")
        if "text/html" not in response.headers.get("Content-Type", ""):
            raise ValueError("Non-HTML response")
        content = response.read(2_000_001)
        if len(content) > 2_000_000:
            raise ValueError("Page too large")
        return content.decode("utf-8", errors="replace")


def run(targets):
    results = {}
    for site, urls in targets.items():
        rows, errors = [], []
        for url in urls:
            host = urlparse(url).hostname or ""
            expected = urlparse(SITES[site]).hostname or ""
            if host != expected and not host.endswith("." + expected):
                errors.append(f"Rejected non-site URL: {url}")
                continue
            if not allowed(url):
                errors.append(f"Robots disallow or cannot verify: {url}")
                continue
            try:
                rows.extend(extract(fetch(url), site, url))
            except Exception as exc:
                errors.append(f"{url}: {type(exc).__name__}: {exc}")
        results[site] = {"products": rows, "errors": errors, "urls_checked": len(urls)}
    return results


def save(results, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "products.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Tablet Probe Report", "", f"Generated UTC: {datetime.now(timezone.utc).isoformat()}", "",
             "| Site | URLs | Products | Field completeness | Errors |", "|---|---:|---:|---:|---:|"]
    for site in SITES:
        info = results.get(site, {"products": [], "errors": [], "urls_checked": 0})
        rows = info["products"]
        completeness = sum(bool(p.get(k)) for p in rows for k in FIELDS) / (len(rows) * len(FIELDS)) * 100 if rows else 0
        lines.append(f"| {site} | {info['urls_checked']} | {len(rows)} | {completeness:.1f}% | {len(info['errors'])} |")
    report = output.parent / "reports" / "probe_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=os.getenv("PROBE_INPUT", "probe/targets.json"))
    parser.add_argument("--output", default="probe/output")
    args = parser.parse_args()
    targets = json.loads(Path(args.input).read_text(encoding="utf-8"))
    unknown = set(targets) - set(SITES)
    if unknown:
        parser.error(f"Unknown sites: {sorted(unknown)}")
    save(run(targets), Path(args.output))


if __name__ == "__main__":
    main()
