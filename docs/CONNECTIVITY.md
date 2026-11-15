# Small connectivity experiment

Run manually from GitHub Actions > Connectivity smoke test > Run workflow.
The test checks one homepage per configured site plus **at most three explicitly supplied product URLs** from `probe/targets.json`.

- `html_accessible_no_product` means an HTML page was fetched, not that a product was extracted.
- `products_found` requires Product JSON-LD. It is still subject to human spot checking.
- `http_error` records status codes such as 403 or 429.
- `robots_blocked_or_unknown` means no fetch was performed.
- `connection_error` captures network errors.

No CAPTCHA bypass, authentication, automated search-engine scraping, or claim of live success. URLs are empty initially, so this first run checks **homepage connectivity only**. Product extraction testing requires verified public product URLs.
