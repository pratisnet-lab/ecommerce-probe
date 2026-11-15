import unittest
from unittest.mock import patch
from probe.discovery_only import discover, is_ipad, is_next_page

class DiscoveryOnlyTests(unittest.TestCase):
    def test_ipad_and_pagination(self):
        self.assertTrue(is_ipad("https://www.n11.com/urun/apple-ipad-123", "iPad"))
        self.assertTrue(is_next_page("https://www.n11.com/tablet?page=2", "2", "https://www.n11.com/tablet?page=1"))
    def test_no_product_detail_requests(self):
        visited = []
        def load(site, url):
            visited.append(url)
            if url.endswith("/tablet"):
                return ('<a href="/urun/apple-ipad-123">Apple iPad</a>', url), "html_accessible"
            return ('<a href="/tablet">Tablet</a>', url), "html_accessible"
        with patch("probe.discovery_only.load_html", side_effect=load), patch("probe.discovery_only.time.sleep"):
            result = discover("amazon", max_pages=5)
        self.assertEqual(result["ipad_count"], 1)
        self.assertFalse(any("/urun/" in url for url in visited))
if __name__ == "__main__":
    unittest.main()
