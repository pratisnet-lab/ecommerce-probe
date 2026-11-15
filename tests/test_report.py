import json
import tempfile
import unittest
from pathlib import Path
from probe.main import save
from probe.sites.catalog import SITES

class ReportTests(unittest.TestCase):
    def test_empty_targets_report_not_configured(self):
        data = {site: {"products": [], "errors": [], "urls_checked": 0} for site in SITES}
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "output"
            save(data, output)
            quality = json.loads((output / "quality.json").read_text(encoding="utf-8"))
            report = (Path(tmp) / "reports" / "probe_report.md").read_text(encoding="utf-8")
            self.assertEqual(len(quality), 13)
            self.assertEqual(quality["amazon"]["status"], "not_configured")
            self.assertIn("| amazon | not_configured |", report)
            self.assertIn("N/A", report)
            self.assertIn("\n| trendyol |", report)

if __name__ == "__main__":
    unittest.main()
