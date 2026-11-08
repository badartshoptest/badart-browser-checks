import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import matterport_probe as probe


class ReportingTests(unittest.TestCase):
    def test_webgl_pass_is_not_tour_pass(self):
        report = probe.new_report()
        report['webgl2'] = 'PASS'
        report['snapshots'] = [{'index': 1}, {'index': 2}]
        self.assertEqual(probe.outcome(report), 2)
        self.assertEqual(report['interior_rendered'], 'NOT VERIFIED')
        self.assertEqual(report['movement_between_stations'], 'NOT VERIFIED')

    def test_empty_is_not_success(self):
        self.assertNotEqual(probe.outcome(probe.new_report()), 0)

    def test_failure_is_not_success(self):
        for key, value in [('webgl2', 'FAIL'), ('errors', [{'type': 'TimeoutException'}])]:
            report = probe.new_report()
            report[key] = value
            self.assertEqual(probe.outcome(report), 1)

    def test_interaction_gate(self):
        gate = dict(recognized_error=False, large_visible_canvas=True, editable_focus=False)
        self.assertTrue(probe.may_interact('PASS', True, gate))
        self.assertFalse(probe.may_interact('FAIL', True, gate))
        self.assertFalse(probe.may_interact('PASS', False, gate))
        self.assertFalse(probe.may_interact('PASS', True, {}))
        for key in gate:
            bad = dict(gate)
            bad[key] = not gate[key]
            self.assertFalse(probe.may_interact('PASS', True, bad))

    def test_destination(self):
        self.assertTrue(probe.expected_url(probe.URL))
        for url in ['http://my.matterport.com/show/?m=Q7ZYcX86N3T',
                    'https://evil.test/show/?m=Q7ZYcX86N3T',
                    'https://my.matterport.com/show/?m=other']:
            self.assertFalse(probe.expected_url(url))

    def test_guard(self):
        env = dict(GITHUB_ACTIONS='true', GITHUB_REPOSITORY='badartshoptest/badart-browser-checks',
                   GITHUB_EVENT_NAME='workflow_dispatch', GITHUB_REF='refs/heads/main',
                   CONFIRMED_RUN='true', REPOSITORY_PUBLIC='true', REPOSITORY_FORK='false')
        self.assertTrue(probe.allowed(env))
        for key in env:
            bad = dict(env)
            bad[key] = 'invalid'
            self.assertFalse(probe.allowed(bad), key)

    def test_output_opt_in_and_no_untrusted_summary(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict('os.environ', {}, clear=True):
            path = Path(tmp) / 'evidence'
            report = probe.new_report()
            report['snapshots'] = [{'visible_inventory': {'label': 'UNTRUSTED_PAGE_TEXT'}}]
            with patch.object(probe, 'OUTPUT', path), contextlib.redirect_stdout(io.StringIO()) as out:
                probe.emit(report, False)
                self.assertFalse(path.exists())
                probe.emit(report, True)
                self.assertTrue((path / 'report.json').is_file())
            self.assertNotIn('UNTRUSTED_PAGE_TEXT', out.getvalue())


if __name__ == '__main__':
    unittest.main()
