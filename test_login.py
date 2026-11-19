import contextlib
import io
import unittest
from unittest.mock import patch, Mock
import check_login
from selenium.common.exceptions import TimeoutException


class LoginPrivacyTests(unittest.TestCase):
    def test_startup_log_redacts_secrets_and_addresses(self):
        output = io.StringIO()
        with patch('pathlib.Path.read_text', return_value='ERROR WebDriverAgent failed private@example.invalid secret-for-test https://host.invalid/path'), contextlib.redirect_stdout(output):
            with patch.dict('os.environ', {}, clear=True):
                check_login.startup_diagnostics('private@example.invalid', 'secret-for-test')
        self.assertIn('WebDriverAgent', output.getvalue())
        for value in ('private@example.invalid', 'secret-for-test', 'host.invalid'):
            self.assertNotIn(value, output.getvalue())
    def test_explicit_access_denial_stops_before_reload_or_credentials(self):
        driver = Mock()
        driver.current_url = 'https://www.badart-shop.de/account/login'
        driver.title = '403 Forbidden'
        driver.execute_script.return_value = []
        waiter = Mock()
        waiter.until.side_effect = TimeoutException()
        with patch('check_login.WebDriverWait', return_value=waiter), patch('check_login.report'):
            with self.assertRaises(RuntimeError):
                check_login.login_controls(driver)
        driver.get.assert_not_called()

    def test_pre_entry_reload_never_types_or_submits(self):
        driver = Mock()
        driver.current_url = 'https://www.badart-shop.de/account/login'
        driver.execute_script.return_value = []
        driver.find_element.return_value.text = ''
        mail, secret = Mock(), Mock()
        waiter = Mock()
        waiter.until.side_effect = [TimeoutException(), True, mail, secret]
        with patch('check_login.WebDriverWait', return_value=waiter), patch('check_login.report'):
            self.assertEqual(check_login.login_controls(driver), (mail, secret))
        driver.get.assert_called_once_with(check_login.BASE + '/account/login')
        mail.send_keys.assert_not_called()
        secret.send_keys.assert_not_called()
        mail.click.assert_not_called()
        secret.click.assert_not_called()

    def test_pre_entry_reload_is_bounded(self):
        driver = Mock()
        driver.current_url = 'https://www.badart-shop.de/account/login'
        driver.execute_script.return_value = []
        driver.find_element.return_value.text = ''
        waiter = Mock()
        waiter.until.side_effect = [TimeoutException(), True, TimeoutException()]
        with patch('check_login.WebDriverWait', return_value=waiter), patch('check_login.report'):
            with self.assertRaises(TimeoutException):
                check_login.login_controls(driver)
        driver.get.assert_called_once_with(check_login.BASE + '/account/login')

    def page(self, path, text='', login=False, logout=False):
        driver = Mock()
        driver.current_url = path
        driver.find_element.return_value.text = text
        driver.find_elements.side_effect = lambda by, selector: [Mock()] if (selector == '#loginMail' and login) or ('/account/logout' in selector and logout) else []
        return driver

    def test_login_form_alone_never_proves_authentication(self):
        self.assertFalse(check_login.login_state(self.page('https://www.badart-shop.de/account/login', login=True)))

    def test_protected_page_is_positive_without_lazy_logout_menu(self):
        self.assertEqual(check_login.login_state(self.page('https://www.badart-shop.de/account', 'Hier haben Sie direkten Zugriff auf Ihre Profilinformationen.')), 'authenticated')

    def test_error_at_protected_url_is_not_authentication(self):
        self.assertFalse(check_login.login_state(self.page('https://www.badart-shop.de/account', '403 Forbidden')))

    def test_unfinished_protected_page_is_not_authentication(self):
        self.assertFalse(check_login.login_state(self.page('https://www.badart-shop.de/account')))

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
