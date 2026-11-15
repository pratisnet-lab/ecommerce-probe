import unittest
from unittest.mock import patch
from probe.full_ipad import crawl_site, category_link, product_link, pagination_link

class FullIpadTests(unittest.TestCase):
    def test_link_classification(self):
        self.assertTrue(category_link("https://www.n11.com/ipad-ve-tablet", "Tablet"))
        self.assertTrue(product_link("https://www.n11.com/urun/apple-ipad-air-123", "iPad Air"))
        self.assertTrue(pagination_link("https://www.n11.com/ipad?page=2", "2", "https://www.n11.com/ipad?page=1"))

    def test_category_and_all_products_no_three_limit(self):
        home = '<a href="/tablet">Tablet</a>'
        listing = "".join(f'<a href="/urun/apple-ipad-{n}">Apple iPad {n}</a>' for n in range(6))
        def load(site, url):
            if url.endswith("/tablet"):
                return (listing, url), "html_accessible"
            if "/urun/" in url:
                number = url.rsplit("-", 1)[-1]
                html = ('<script type="application/ld+json">'
                        '{"@type":"Product","name":"Apple iPad '+number+'",'
                        '"offers":{"price":"100","priceCurrency":"TRY"}}'
                        '</script>')
                return (html, url), "html_accessible"
            return (home, url), "html_accessible"
        with patch("probe.full_ipad.load_html", side_effect=load), patch("probe.full_ipad.time.sleep"):
            result = crawl_site("amazon", max_pages=10, max_requests=20)
        self.assertEqual(len(result["product_urls"]), 6)
        self.assertEqual(len(result["products"]), 6)
        self.assertTrue(result["complete"])
        self.assertEqual(result["products_with_price"], 6)
        self.assertEqual(result["error_count"], 0)

    def test_no_products_cannot_be_complete(self):
        with patch("probe.full_ipad.load_html", return_value=('<a href="/tablet">Tablet</a>', "https://www.amazon.com.tr")), patch("probe.full_ipad.time.sleep"):
            result = crawl_site("amazon", max_requests=4)
        self.assertFalse(result["complete"])

    def test_budget_marks_incomplete(self):
        with patch("probe.full_ipad.load_html", return_value=('<a href="/tablet">Tablet</a>', "https://www.amazon.com.tr")), patch("probe.full_ipad.time.sleep"):
            result = crawl_site("amazon", max_requests=1)
        self.assertFalse(result["complete"])

if __name__ == "__main__":
    unittest.main()
