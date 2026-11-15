"""Pure functions for assessing collected product records."""
from probe.sites.extract import FIELDS

def evaluate(results):
    summary = {}
    for site, info in results.items():
        products = info.get("products", [])
        urls = info.get("urls_checked", 0)
        errors = info.get("errors", [])
        completeness = (
            round(100 * sum(bool(row.get(field)) for row in products for field in FIELDS)
                  / (len(products) * len(FIELDS)), 2)
            if products else None
        )
        status = ("not_configured" if not urls else
                  "products_found_with_errors" if products and errors else
                  "products_found" if products else
                  "failed" if errors else "no_structured_products")
        summary[site] = {
            "status": status, "urls_checked": urls, "products": len(products),
            "errors": len(errors), "field_completeness_percent": completeness,
            "missing_fields": {
                field: sum(not bool(row.get(field)) for row in products)
                for field in FIELDS
            },
        }
    return summary
