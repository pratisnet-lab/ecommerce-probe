import unittest
from probe.sites.extract import extract

class ExtractTests(unittest.TestCase):
    def test_json_ld(self):
        html = '<script type="application/ld+json">{"@type":"Product","name":"Tablet","brand":{"name":"Example"},"offers":{"price":"100","priceCurrency":"TRY","availability":"https://schema.org/InStock"}}</script>'
        rows = extract(html, "amazon", "https://www.amazon.com.tr/item")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Tablet")
        self.assertEqual(rows[0]["currency"], "TRY")

    def test_invalid_json(self):
        self.assertEqual(extract('<script type="application/ld+json">{bad}</script>', "amazon", "https://www.amazon.com.tr"), [])

if __name__ == "__main__":
    unittest.main()
