import contextlib
import io
import unittest
from unittest.mock import patch, Mock
import check_login


class LoginPrivacyTests(unittest.TestCase):
    def page(self, path, text='', login=False, logout=False):
        driver = Mock()
        driver.current_url = path
        driver.find_element.return_value.text = text
        driver.find_elements.side_effect = lambda by, selector: [Mock()] if (selector == '#loginMail' and login) or ('/account/logout' in selector and logout) else []
        return driver

    def test_login_form_alone_never_proves_authentication(self):
        self.assertFalse(check_login.login_state(self.page('https://www.badart-shop.de/account/login', login=True)))

    def test_protected_page_is_positive_without_lazy_logout_menu(self):
        self.assertEqual(check_login.login_state(self.page('https://www.badart-shop.de/account')), 'authenticated')

    def test_external_origin_cannot_be_accepted(self):
        self.assertEqual(check_login.login_state(self.page('https://other.invalid/account', logout=True)), 'unexpected_origin')

    def test_explicit_rejection_is_not_hidden_as_timeout(self):
        self.assertEqual(check_login.login_state(self.page('https://www.badart-shop.de/account/login', 'Es konnte kein Account mit den angegebenen Zugangsdaten gefunden werden.', login=True)), 'rejected')

    def test_missing_secrets_never_starts_browser(self):
        with patch.dict('os.environ', {}, clear=True), patch('check_login.create_driver') as start, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_login.run(), 2)
            start.assert_not_called()

    def test_errors_do_not_print_secrets_or_exception_messages(self):
        output = io.StringIO()
        with patch.dict('os.environ', {'SHOP_TEST_EMAIL': 'private@example.invalid', 'SHOP_TEST_PASSWORD': 'secret-for-test'}, clear=True), patch('check_login.create_driver', side_effect=RuntimeError('private@example.invalid secret-for-test')), contextlib.redirect_stdout(output):
            self.assertEqual(check_login.run(), 2)
        self.assertNotIn('private@example.invalid', output.getvalue())
        self.assertNotIn('secret-for-test', output.getvalue())


if __name__ == '__main__':
    unittest.main()
