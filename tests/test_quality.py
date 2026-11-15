import unittest
from probe.quality import evaluate

class QualityTests(unittest.TestCase):
    def test_unconfigured_is_not_success(self):
        result = evaluate({"amazon": {"products": [], "errors": [], "urls_checked": 0}})
        self.assertEqual(result["amazon"]["status"], "not_configured")
        self.assertIsNone(result["amazon"]["field_completeness_percent"])

    def test_errors_are_not_zero_products(self):
        result = evaluate({"n11": {"products": [], "errors": ["403"], "urls_checked": 1}})
        self.assertEqual(result["n11"]["status"], "failed")

    def test_product_completeness(self):
        result = evaluate({"vatan": {"products": [{"site": "vatan", "title": "Tablet"}], "errors": [], "urls_checked": 1}})
        self.assertEqual(result["vatan"]["status"], "products_found")
        self.assertEqual(result["vatan"]["field_completeness_percent"], 20.0)

if __name__ == "__main__":
    unittest.main()
