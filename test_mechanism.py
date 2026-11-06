"""Test fail-closed reporting and simulator selection without a shop session."""
import unittest
from check_shop import outcome, safe_text
from mobile_setup import choose_ios


class MechanismTests(unittest.TestCase):
    def test_no_results_cannot_pass(self):
        self.assertEqual(outcome([]), 2)

    def test_blocked_session_cannot_pass(self):
        self.assertEqual(outcome([{"status": "PASS"}, {"status": "BLOCKED"}]), 2)

    def test_failed_assertion_fails_job(self):
        self.assertEqual(outcome([{"status": "PASS"}, {"status": "FAIL"}]), 1)

    def test_valid_baseline_can_pass(self):
        self.assertEqual(outcome([{"status": "PASS"}]), 0)

    def test_version_text_cannot_inject_report_markup(self):
        self.assertNotIn("|", safe_text("Safari|PASS\n<script>"))

    def test_simulator_selects_available_target_latest_runtime(self):
        data = {"devices": {
            "com.apple.CoreSimulator.SimRuntime.iOS-18-5": [
                {"name": "iPhone 16", "isAvailable": True, "udid": "old"}],
            "com.apple.CoreSimulator.SimRuntime.iOS-26-1": [
                {"name": "iPhone 17", "isAvailable": False, "udid": "unavailable"},
                {"name": "iPad Pro", "isAvailable": True, "udid": "ipad"}],
        }}
        self.assertEqual(choose_ios(data, "iphone")["appium:udid"], "old")
        self.assertEqual(choose_ios(data, "ipad")["appium:platformVersion"], "26.1")
        with self.assertRaises(RuntimeError):
            choose_ios({"devices": {}}, "iphone")


if __name__ == "__main__":
    unittest.main()
