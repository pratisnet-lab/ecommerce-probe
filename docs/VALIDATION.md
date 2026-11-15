# Validation protocol

## Current status
The 13 storefront names are configured, but **no live URL has been validated**.
The default `probe/targets.json` deliberately contains empty URL lists.
A successful GitHub Actions run means the Python job completed; it **does not** prove any product was collected.

## Site onboarding
1. Confirm the site's terms, permitted access method, and robots.txt rules.
2. Supply a public tablet product page URL in `probe/targets.json`.
3. Run the probe manually, inspect errors and product data.
4. Verify title, price, currency, URL, image, brand, EAN, MPN and availability against the page.
5. Only then mark the site as operational. Do not infer EAN/MPN when absent.
6. Prefer authorized feeds/APIs where scraping is restricted.

## Interpretation
- 0 products means no extracted product, not necessarily zero listings.
- Field completeness applies only to extracted products.
- Robots verification failure blocks the fetch.
- Some websites rely on JavaScript, login, or anti-bot controls; this baseline intentionally does not bypass them.
- Google Drive export remains out of scope until its destination and credentials are configured securely.
