import unittest
from probe.discovery import candidates

class DiscoveryTests(unittest.TestCase):
    def test_extract_only_ipad_product_links(self):
        html = ('<a href="/apple-ipad-a16-p-123">iPad</a>'
                '<a href="/apple-macbook-p-456">Macbook</a>'
                '<a href="https://evil.example/ipad-p-789">iPad</a>'
                '<a href="/apple-ipad-a16-p-123">duplicate</a>')
        result = candidates("teknosa", html, "https://www.teknosa.com/apple-bilgisayar-tablet-bc-116")
        self.assertEqual(result, ["https://www.teknosa.com/apple-ipad-a16-p-123"])
if __name__ == "__main__":
    unittest.main()
