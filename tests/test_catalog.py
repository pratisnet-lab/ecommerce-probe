import unittest
from probe.sites.catalog import SITES
from probe.sites.extract import FIELDS, extract

class CatalogTests(unittest.TestCase):
    def test_thirteen_distinct_sites(self):
        self.assertEqual(len(SITES), 13)
        self.assertEqual(len(set(SITES.values())), 13)
        self.assertTrue(all(v.startswith("https://") for v in SITES.values()))

    def test_field_contract(self):
        html = '<script type="application/ld+json">{"@graph":[{"@type":"Product","name":"Tablet X","gtin13":"1234567890123","mpn":"ABC-1","brand":{"name":"Brand X"},"image":["/tablet.jpg"],"offers":[{"price":1999,"priceCurrency":"TRY"}]}]}</script>'
        products = extract(html, "teknosa", "https://www.teknosa.com/item")
        self.assertEqual(len(products), 1)
        self.assertEqual(set(products[0]), set(FIELDS))
        self.assertEqual(products[0]["ean"], "1234567890123")
        self.assertEqual(products[0]["mpn"], "ABC-1")
        self.assertEqual(products[0]["image"], "https://www.teknosa.com/tablet.jpg")

    def test_no_products_is_not_success(self):
        self.assertEqual(extract("<html></html>", "amazon", "https://www.amazon.com.tr/item"), [])

if __name__ == "__main__":
    unittest.main()
