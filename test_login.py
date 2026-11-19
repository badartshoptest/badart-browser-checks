import contextlib
import io
import unittest
from unittest.mock import patch
import check_login


class LoginPrivacyTests(unittest.TestCase):
    def test_missing_secrets_never_starts_browser(self):
        with patch.dict('os.environ', {}, clear=True), patch('check_login.create_driver') as start, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_login.run(), 2)
            start.assert_not_called()

    def test_errors_do_not_print_secrets_or_exception_messages(self):
        output = io.StringIO()
        with patch.dict('os.environ', {'SHOP_TEST_EMAIL': 'private@example.invalid', 'SHOP_TEST_PASSWORD': 'secret-for-test'}), patch('check_login.create_driver', side_effect=RuntimeError('private@example.invalid secret-for-test')), contextlib.redirect_stdout(output):
            self.assertEqual(check_login.run(), 2)
        self.assertNotIn('private@example.invalid', output.getvalue())
        self.assertNotIn('secret-for-test', output.getvalue())


if __name__ == '__main__':
    unittest.main()
