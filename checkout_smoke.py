"""Unauthenticated, GET-only storefront probe. No browser script, forms, or orders."""
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ORIGIN = "https://www.badart-shop.de"
ROUTES = frozenset({"/checkout/cart", "/checkout/confirm", "/checkout/register", "/account/login"})
LIMIT = 2_000_000


class UnsafeRoute(Exception):
    pass


class StopRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def checked_url(url):
    u = urlsplit(url)
    if (u.scheme, u.netloc) != ("https", "www.badart-shop.de") or u.path not in ROUTES or u.query or u.fragment:
        raise UnsafeRoute()
    return url


def public_get(path, opener=None):
    opener = opener or build_opener(StopRedirect())
    url = checked_url(ORIGIN + path)
    for _ in range(3):
        try:
            with opener.open(Request(url, method="GET"), timeout=12) as response:
                if response.geturl() != url:
                    return "BLOCKED", "unexpected automatic redirect", ""
                if "text/html" not in response.headers.get("Content-Type", "").lower():
                    return "BLOCKED", "unexpected response format", ""
                body = response.read(LIMIT + 1)
                if len(body) > LIMIT:
                    return "BLOCKED", "response exceeds inspection limit", ""
                return "OK", urlsplit(url).path, body.decode("utf-8", "replace")
        except HTTPError as exc:
            with exc:
                if exc.code in (301, 302, 303, 307, 308) and exc.headers.get("Location"):
                    url = checked_url(urljoin(url, exc.headers["Location"]))
                    continue
                return "BLOCKED", f"HTTP {exc.code}", ""
        except (OSError, URLError):
            return "BLOCKED", "network or TLS error", ""
    return "BLOCKED", "redirect limit reached", ""


class ShopMarkers(HTMLParser):
    def __init__(self):
        super().__init__()
        self.main = False
        self.order_form = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.main |= attrs.get("id") == "content-main"
        if tag == "form":
            action = attrs.get("action") or ""
            self.order_form |= urlsplit(action).path.rstrip("/") == "/checkout/order"


def classify(path, body, *, expect_review):
    if not body or any(x in body.lower() for x in (
        "<title>just a moment", "verify you are human", "checking your browser"
    )):
        return "BLOCKED", "empty response or challenge"
    markers = ShopMarkers()
    markers.feed(body)
    if not markers.main:
        return "BLOCKED", "storefront marker missing"
    if expect_review:
        if path == "/checkout/confirm" and markers.order_form:
            return "PASS", "review markup reached; stopped without submitting"
        return "BLOCKED", "review not reached in public session"
    if path != "/checkout/cart" or markers.order_form:
        return "FAIL", "unexpected cart state"
    return "PASS", "cart page reached without mutation"


def probe(path, *, expect_review=False, get=public_get):
    try:
        status, result, body = get(path)
        return classify(result, body, expect_review=expect_review) if status == "OK" else (status, result)
    except UnsafeRoute:
        return "BLOCKED", "redirect outside the approved route list"


def main():
    cart = probe("/checkout/cart")
    print(f"Cart: {cart[0]} ({cart[1]})")
    if cart[0] != "PASS":
        return 2
    review = probe("/checkout/confirm", expect_review=True)
    print(f"Review route: {review[0]} ({review[1]})")
    print("No account, cart change, order, payment or email was sent.")
    return 0 if review[0] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
