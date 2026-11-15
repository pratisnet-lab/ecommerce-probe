import unittest
from probe.smoke_summary import render

class SmokeSummaryTests(unittest.TestCase):
    def test_homepage_is_not_product_success(self):
        data = {"sites": {"amazon": [
            {"http_status": 200, "status": "html_accessible_no_product", "products": []}
        ]}}
        report = render(data)
        self.assertIn("| amazon | 200 | html_accessible_no_product | 0 | 0 |", report)

    def test_requires_name_and_price(self):
        data = {"sites": {"n11": [
            {"http_status": 200, "status": "html_accessible_no_product", "products": []},
            {"http_status": 200, "status": "products_found", "products": [{"title": "Tablet", "price": None}]},
            {"http_status": 200, "status": "products_found", "products": [{"title": "Tablet", "price": "100"}]},
        ]}}
        self.assertIn("| n11 | 200 | html_accessible_no_product | 2 | 1 |", render(data))

if __name__ == "__main__":
    unittest.main()
