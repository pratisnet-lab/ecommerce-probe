import sqlite3
import tempfile
import unittest
from pathlib import Path
from probe.storage import save_report

class StorageTests(unittest.TestCase):
    def test_upsert_keeps_one_product_and_tracks_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "products.sqlite")
            report = {"sites": {"trendyol": {
                "status": "partial_products", "complete": False, "errors": [],
                "products": [{"url": "https://www.trendyol.com/ipad-p-1",
                              "title": "Apple iPad", "price": "100", "currency": "TRY"}]}}}
            save_report(report, path)
            report["sites"]["trendyol"]["products"][0]["price"] = "120"
            save_report(report, path)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM products").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT price FROM products").fetchone()[0], "120")
                self.assertEqual(db.execute("SELECT COUNT(*) FROM crawl_runs").fetchone()[0], 2)
if __name__ == "__main__":
    unittest.main()
