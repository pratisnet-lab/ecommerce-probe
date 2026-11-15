"""Write a readable GitHub Actions summary from actual smoke-test results."""
import json
import os
from pathlib import Path

def render(data):
    lines = [
        "## Ecommerce Probe — connection smoke test",
        "",
        "A successful job is **not** proof of product extraction.",
        "",
        "| Site | Homepage HTTP | Homepage result | Product URLs | Verified name + price |",
        "|---|---:|---|---:|---:|",
    ]
    for site, checks in data["sites"].items():
        homepage = checks[0]
        product_checks = checks[1:]
        verified = sum(
            any(p.get("title") and p.get("price") is not None for p in check["products"])
            for check in product_checks
        )
        code = homepage["http_status"] if homepage["http_status"] is not None else "—"
        lines.append(
            f"| {site} | {code} | {homepage['status']} | "
            f"{len(product_checks)} | {verified} |"
        )
    lines += ["", "A product is provisionally verified only when both title and price are present.",
              "Review source pages manually before treating extraction as production-ready.", ""]
    return "\n".join(lines)

def main():
    data = json.loads(Path("probe/output/connectivity.json").read_text(encoding="utf-8"))
    markdown = render(data)
    print(markdown)
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(markdown)

if __name__ == "__main__":
    main()
