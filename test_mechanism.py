"""Test fail-closed reporting and simulator selection without a shop session."""
import unittest
import subprocess
from unittest.mock import Mock, patch
import json
from unittest.mock import mock_open
from selenium.webdriver.common.by import By
from check_shop import create_driver
from check_shop import outcome, safe_text
from mobile_setup import choose_ios, wait_for_android_boot, choose_xcuitest_version


class MechanismTests(unittest.TestCase):
    def test_xcode_gets_a_pinned_compatible_driver(self):
        self.assertEqual(choose_xcuitest_version('Xcode 16.4\nBuild version 16F6'), '12.12.4')
        self.assertEqual(choose_xcuitest_version('Xcode 26.5'), '12.22.8')
        self.assertEqual(choose_xcuitest_version('Xcode 27.0'), '12.22.8')

    def test_unknown_or_old_xcode_is_not_silently_accepted(self):
        for value in ('Xcode 15.4', 'unexpected output'):
            with self.assertRaises(RuntimeError):
                choose_xcuitest_version(value)

    def test_mobile_web_session_converts_id_to_w3c_css(self):
        with patch('check_shop.TARGET', 'android-phone'), \
                patch('pathlib.Path.read_text', return_value=json.dumps({'browserName': 'Chrome'})), \
                patch('appium.webdriver.Remote') as remote:
            driver = create_driver()
            self.assertEqual(remote.call_args.kwargs['client_config'].timeout, 240)
            self.assertEqual(driver.locator_converter.convert(By.ID, 'accountType'),
                             ('css selector', '[id="accountType"]'))
            self.assertEqual(driver.locator_converter.convert(By.XPATH, './/option'),
                             ('xpath', './/option'))

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


