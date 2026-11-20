import io
import unittest
from urllib.error import HTTPError
from unittest.mock import Mock

from checkout_smoke import ORIGIN, UnsafeRoute, checked_url, probe, public_get


class CheckoutSmokeTest(unittest.TestCase):
    def test_rejects_submissions_and_external_urls(self):
        for suffix in ("/checkout/order", "/checkout/finish", "/checkout/confirm?x=1", "/checkout/confirm#x"):
            with self.subTest(suffix=suffix), self.assertRaises(UnsafeRoute):
                checked_url(ORIGIN + suffix)
        with self.assertRaises(UnsafeRoute):
            checked_url("https://other.invalid/checkout/cart")

    def test_redirect_to_order_is_never_requested(self):
        opener = Mock()
        opener.open.side_effect = HTTPError(ORIGIN + "/checkout/confirm", 302, "", {"Location": "/checkout/order"}, io.BytesIO())
        with self.assertRaises(UnsafeRoute):
            public_get("/checkout/confirm", opener)
        self.assertEqual(opener.open.call_count, 1)
        self.assertEqual(opener.open.call_args.args[0].get_method(), "GET")

    def test_403_stops_without_retry_or_echo(self):
        opener = Mock()
        opener.open.side_effect = HTTPError(ORIGIN + "/checkout/cart", 403, "", {}, io.BytesIO(b"do not log"))
        self.assertEqual(public_get("/checkout/cart", opener), ("BLOCKED", "HTTP 403", ""))
        self.assertEqual(opener.open.call_count, 1)

    def test_checkout_review_is_diagnosed_without_form_interaction(self):
        get = Mock(return_value=("OK", "/checkout/confirm",
                                 '<main id="content-main"><form action="/checkout/order" method="post"></form></main>'))
        self.assertEqual(probe("/checkout/confirm", expect_review=True, get=get)[0], "PASS")
        get.assert_called_once_with("/checkout/confirm")

    def test_cart_and_signin_are_not_review_passes(self):
        for route in ("/checkout/cart", "/account/login", "/checkout/register"):
            get = Mock(return_value=("OK", route, '<main id="content-main"></main>'))
            self.assertEqual(probe("/checkout/confirm", expect_review=True, get=get)[0], "BLOCKED")

    def test_challenge_is_not_a_pass(self):
        get = Mock(return_value=("OK", "/checkout/cart",
                                 '<title>Just a moment...</title><main id="content-main"></main>'))
        self.assertEqual(probe("/checkout/cart", get=get)[0], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
