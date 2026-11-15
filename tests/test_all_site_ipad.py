import unittest
from probe.all_site_ipad import links_for, choose_categories, choose_products
from probe.sites.catalog import SITES

class AllSiteDiscoveryTests(unittest.TestCase):
    def test_all_thirteen_sites_in_scope(self):
        self.assertEqual(len(SITES), 13)
    def test_discovery_filters_external_and_categories(self):
        html = ('<a href="/apple-tablet">Apple Tablet</a>'
                '<a href="/apple-ipad-air-p-123">Apple iPad Air</a>'
                '<a href="https://evil.example/ipad-p-9">iPad</a>')
        links = links_for("trendyol", html, "https://www.trendyol.com/")
        self.assertEqual(choose_products(links), ["https://www.trendyol.com/apple-ipad-air-p-123"])
        self.assertEqual(choose_categories(links), ["https://www.trendyol.com/apple-tablet"])
    def test_no_invented_product_urls(self):
        self.assertEqual(choose_products([]), [])
if __name__ == "__main__":
    unittest.main()
