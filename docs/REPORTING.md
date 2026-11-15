# Reporting contract

Running `python -m probe.main` creates:
- `probe/output/products.json`: collected records and request errors
- `probe/output/quality.json`: site status, counts, missing-field counts, completeness
- `probe/reports/probe_report.md`: human-readable table

A site with no configured URLs is `not_configured` and its completeness is `N/A`, not 0%.
A successful scheduled job does not establish that any site is operational.

The scheduled workflow uploads all three files as an artifact. No Google Drive integration is configured.
