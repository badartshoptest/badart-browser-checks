"""Test fail-closed reporting and simulator selection without a shop session."""
import unittest
import subprocess
from unittest.mock import Mock, patch
from check_shop import outcome, safe_text
from mobile_setup import choose_ios, wait_for_android_boot


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
        self.assertEqual(choose_ios(data, "iphone", max_major=18)["appium:platformVersion"], "18.5")
        with self.assertRaises(RuntimeError):
            choose_ios(data, "ipad", max_major=18)
        with self.assertRaises(RuntimeError):
            choose_ios({"devices": {}}, "iphone")


class AndroidBootTests(unittest.TestCase):
    def wait_with_results(self, results, timeout=30, emulator_exit=None):
        clock = [0.0]
        def sleep(seconds):
            clock[0] += seconds
        emulator = Mock()
        emulator.poll.return_value = emulator_exit
        with patch("mobile_setup.time.monotonic", side_effect=lambda: clock[0]), \
                patch("mobile_setup.time.sleep", side_effect=sleep), \
                patch("mobile_setup.subprocess.run", side_effect=results) as probe:
            wait_for_android_boot("adb", emulator, timeout=timeout)
        return probe

    def test_transient_offline_does_not_abort_boot(self):
        ready = subprocess.CompletedProcess([], 0, "1\n", "")
        offline = subprocess.CompletedProcess([], 1, "", "adb: device offline")
        booting = subprocess.CompletedProcess([], 0, "\n", "")
        probe = self.wait_with_results([offline, booting, ready, offline, ready, ready])
        self.assertEqual(probe.call_count, 6)
        self.assertEqual(probe.call_args.args[0],
                         ["adb", "-s", "emulator-5554", "shell", "getprop", "sys.boot_completed"])
        self.assertLessEqual(probe.call_args.kwargs["timeout"], 15)

    def test_probe_timeout_is_retried(self):
        ready = subprocess.CompletedProcess([], 0, "1", "")
        self.wait_with_results([subprocess.TimeoutExpired("adb", 15), ready, ready])

    def test_permanent_offline_fails_closed_at_deadline(self):
        offline = subprocess.CompletedProcess([], 1, "", "adb: device offline")
        with self.assertRaisesRegex(RuntimeError, "boot timeout"):
            self.wait_with_results([offline] * 4, timeout=10)

    def test_emulator_exit_fails_without_probing(self):
        with self.assertRaisesRegex(RuntimeError, "emulator exited"):
            self.wait_with_results([], emulator_exit=1)

    def test_unauthorized_and_unexpected_errors_are_not_retried(self):
        for error in ("device unauthorized", "unknown command"):
            with self.subTest(error=error), self.assertRaises(RuntimeError):
                self.wait_with_results([subprocess.CompletedProcess([], 1, "", error)])


if __name__ == "__main__":
    unittest.main()

