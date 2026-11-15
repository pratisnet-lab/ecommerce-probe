import unittest
from unittest.mock import patch
from probe.connectivity import check

class ConnectivityTests(unittest.TestCase):
    def test_non_https_rejected_without_request(self):
        with patch("probe.connectivity.urlopen") as urlopen:
            result = check("amazon", "http://www.amazon.com.tr/product")
        self.assertEqual(result["status"], "invalid_url")
        urlopen.assert_not_called()

    def test_foreign_domain_rejected(self):
        result = check("amazon", "https://www.amazon.com.tr.evil.example/item")
        self.assertEqual(result["status"], "invalid_url")

    def test_robots_blocked(self):
        with patch("probe.connectivity.RobotFileParser") as robot:
            robot.return_value.can_fetch.return_value = False
            result = check("amazon", "https://www.amazon.com.tr/item")
        self.assertEqual(result["status"], "robots_blocked_or_unknown")

if __name__ == "__main__":
    unittest.main()
