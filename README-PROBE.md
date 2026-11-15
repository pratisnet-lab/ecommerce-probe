# Ecommerce Probe — Tablet foundation

Initial, deliberately conservative implementation. **No live product counts are claimed.**

- Targets: 13 Turkish ecommerce sites listed in `probe/sites/catalog.py`.
- Add explicit, publicly accessible product URLs to `probe/targets.json` per site.
- Run: `python -m probe.main`
- Test: `python -m unittest discover -s tests`
- Output: `probe/output/products.json`, `probe/reports/probe_report.md`.
- Daily GitHub Actions schedule: 23:00 UTC = 02:00 Türkiye next day.
- Extracts Product JSON-LD only. It does not defeat CAPTCHA, authenticate, or bypass access restrictions.
- Fails closed when robots.txt cannot be checked. Empty target lists produce zero results, not fabricated products.
- Many stores may require APIs, permission, or tailored parsers. Google Drive export is **not yet configured**.

Next: verify sample URLs and per-site accessibility before adding custom adapters.
