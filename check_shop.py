"""Public storefront checks. No account creation, login submission, email or order."""
import collections
import json
import os
import platform
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = "https://www.badart-shop.de"
TARGET = os.environ.get("TARGET", "chrome")
CONSENT = os.environ.get("CONSENT", "necessary")
REPORT = {"target": TARGET, "consent": CONSENT, "started": datetime.now(timezone.utc).isoformat(),
          "scope": "Public storefront baseline; not a full purchase certification",
          "environment": {}, "checks": [], "not_tested": [
              "Successful account registration and login", "Password reset email delivery",
              "Cart with a paid product and checkout totals", "Payment completion and return",
              "Apple Pay, bank app switching, passkeys and real device hardware",
              "Every historic browser/OS version", "Autofill with saved customer data"]}


class Blocked(Exception):
    pass


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def safe_text(value):
    # Only used for controlled labels / technical version strings, never HTML or exceptions.
    return re.sub(r"[^a-zA-Z0-9 .,_:/()@+\-]", "", str(value))[:180]


def outcome(rows):
    if not rows or any(r["status"] == "BLOCKED" for r in rows):
        return 2
    return 1 if any(r["status"] == "FAIL" for r in rows) else 0


def create_driver():
    if TARGET == "safari":
        require(platform.system() == "Darwin", "Safari requires macOS")
        return webdriver.Safari()
    if TARGET in ("iphone", "ipad", "android-phone", "android-tablet"):
        from appium import webdriver as mobile_webdriver
        from appium.options.common import AppiumOptions
        caps = json.loads(Path("mobile-capabilities.json").read_text())
        return mobile_webdriver.Remote("http://127.0.0.1:4723", options=AppiumOptions().load_capabilities(caps))
    options_cls, driver_cls = {
        "chrome": (webdriver.ChromeOptions, webdriver.Chrome),
        "edge": (webdriver.EdgeOptions, webdriver.Edge),
        "firefox": (webdriver.FirefoxOptions, webdriver.Firefox),
    }[TARGET]
    options = options_cls()
    options.add_argument("-headless" if TARGET == "firefox" else "--headless=new")
    if TARGET in ("chrome", "edge"):
        options.add_argument("--disable-dev-shm-usage")
    return driver_cls(options=options)


def write_report():
    REPORT["finished"] = datetime.now(timezone.utc).isoformat()
    REPORT["baseline_exit_code"] = outcome(REPORT["checks"])
    Path("result.json").write_text(json.dumps(REPORT, indent=2), encoding="utf-8")
    lines = [f"## {TARGET} / {CONSENT}", "", "Baseline only. Full registration/payment acceptance remains OPEN.", "",
             "Environment: " + json.dumps(REPORT["environment"], sort_keys=True), "",
             "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f'| {r["name"]} | {r["status"]} | {r["detail"]} |' for r in REPORT["checks"]]
    lines += ["", "Not tested:"] + ["- " + x for x in REPORT["not_tested"]]
    text = "\n".join(lines) + "\n"
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(text)


def run():
    driver = None
    try:
        try:
            driver = create_driver()
        except Exception as exc:
            # This occurs before opening the shop: only a bounded, sanitized setup diagnostic.
            message = str(exc).split("Stacktrace:")[0].split("Original error:")[-1]
            message = re.sub(r"https?://\S+|[\w.+-]+@[\w.-]+", "[redacted]", message)
            REPORT["checks"].append({"name": "Driver startup diagnostic", "status": "BLOCKED", "detail": safe_text(message)})
            raise
        caps = driver.capabilities
        REPORT["environment"] = {k: safe_text(caps.get(k, "not reported")) for k in
                                 ("browserName", "browserVersion", "platformName", "platformVersion")}
        REPORT["environment"]["runner_os"] = safe_text(platform.platform())
        REPORT["environment"]["device_kind"] = (
            "Apple simulator" if TARGET in ("iphone", "ipad") else
            "Android emulator" if TARGET.startswith("android-") else "Desktop browser on hosted runner")
        if TARGET in ("iphone", "ipad", "android-phone", "android-tablet"):
            requested = json.loads(Path("mobile-capabilities.json").read_text())
            REPORT["environment"]["device_name"] = safe_text(requested["appium:deviceName"])
            REPORT["environment"]["requested_os_version"] = safe_text(requested.get("appium:platformVersion", "Android 15"))
        expected = "safari" if TARGET in ("safari", "iphone", "ipad") else "chrome" if TARGET.startswith("android-") else TARGET
        actual = str(caps.get("browserName", "")).lower().replace("microsoftedge", "edge")
        require(actual == expected, "Unexpected browser engine")
        wait = WebDriverWait(driver, 20, ignored_exceptions=(StaleElementReferenceException,))
        operation = {"name": "Browser initialization"}
        driver.set_page_load_timeout(50)
        if TARGET in ("chrome", "edge", "firefox", "safari"):
            driver.set_window_size(1440, 1000)

        def visible(selector):
            operation["name"] = "Visible control " + selector
            return wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))

        def click(selector):
            element = visible(selector)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'})", element)
            element.click()

        def accept_consent():
            wanted = ["Nur notwendige", "Nur technisch notwendige", "Nur technisch notwendige Cookies", "Ablehnen"] if CONSENT == "necessary" else ["Alle akzeptieren", "Alle Cookies akzeptieren"]
            element = driver.execute_script("return Array.from(document.querySelectorAll('button, a.btn')).find(e => e.getClientRects().length && arguments[0].includes(e.innerText.trim())) || null", wanted)
            if element is not None:
                element.click()
                return "Consent control clicked"
            # No success claim about consent if a fresh session has no matching control.
            return "No matching consent control visible"

        def open_page(path):
            operation["name"] = "Open " + path
            driver.get(BASE + path)
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            require(urlsplit(driver.current_url).hostname in ("www.badart-shop.de", "badart-shop.de"), "Unexpected navigation origin")
            body = driver.execute_script("return document.body.innerText").lower()
            if any(s in body for s in ("verify you are human", "checking your browser", "access denied", "just a moment")):
                raise Blocked("Site security challenge")
            accept_consent()
            visible("#content-main")
            # Wait for the initial storefront hydration, without masking failed assertions.
            stable = {"signature": None, "since": time.monotonic()}
            def content_settled(d):
                signature = d.execute_script("const e=document.querySelector('#content-main'); return e ? [location.href,e.textContent.length,e.childElementCount] : null")
                if signature != stable["signature"]:
                    stable.update(signature=signature, since=time.monotonic())
                return signature is not None and time.monotonic() - stable["since"] >= 0.8
            wait.until(content_settled)

        def check(name, fn):
            try:
                retries = 0
                try:
                    detail = fn()
                except StaleElementReferenceException:
                    # These checks never submit, order or send mail. Reload once after hydration.
                    retries = 1
                    detail = fn()
                REPORT["checks"].append({"name": name, "status": "PASS", "detail": (detail or "Verified") + ("; DOM refresh retry" if retries else "")})
            except Blocked as exc:
                REPORT["checks"].append({"name": name, "status": "BLOCKED", "detail": str(exc)})
                raise
            except AssertionError as exc:
                REPORT["checks"].append({"name": name, "status": "FAIL", "detail": str(exc)})
            except Exception as exc:
                REPORT["checks"].append({"name": name, "status": "BLOCKED", "detail": type(exc).__name__ + "; " + operation["name"]})
            finally:
                print("CHECK " + json.dumps(REPORT["checks"][-1]), flush=True)

        def consent_choice():
            driver.get(BASE + "/account/login")
            WebDriverWait(driver, 20, ignored_exceptions=(StaleElementReferenceException,)).until(
                lambda d: accept_consent() == "Consent control clicked",
                "Requested consent control not observed; consent coverage unverified")
            return "Requested cookie choice clicked in fresh session"
        check("Cookie choice", consent_choice)

        def fields():
            open_page("/account/login")
            REPORT["environment"]["user_agent"] = safe_text(driver.execute_script("return navigator.userAgent"))
            for field in ("loginMail", "loginPassword", "personalFirstName", "personalLastName", "personalMail", "personalPassword", "personalPasswordConfirmation"):
                require(bool(visible("#" + field).get_property("required")), "Missing required field: " + field)
            return "Login and registration required controls visible"
        check("Required fields", fields)

        def email():
            open_page("/account/login")
            element = visible("#loginMail")
            element.send_keys("ungueltig")
            require(driver.execute_script("return arguments[0].validity.typeMismatch", element), "Invalid email format not detected")
            element.clear()
            require(driver.execute_script("return arguments[0].validity.valueMissing", element), "Empty email not detected")
            return "Browser constraints checked; no submit"
        check("Email format and empty value", email)

        def company():
            open_page("/account/login")
            Select(visible("#accountType")).select_by_visible_text("Gewerblich")
            require(bool(visible("#billingAddresscompany").get_property("required")), "Company not required")
            Select(visible("#accountType")).select_by_visible_text("Privat")
            wait.until(EC.invisibility_of_element_located((By.ID, "billingAddresscompany")))
            return "Company controls toggle correctly"
        check("Private and company registration", company)

        def shipping():
            open_page("/account/login")
            click("#differentShippingAddress")
            visible("#shippingAddresspersonalFirstName")
            click("#differentShippingAddress")
            wait.until(EC.invisibility_of_element_located((By.ID, "shippingAddresspersonalFirstName")))
        check("Different shipping address", shipping)

        def countries():
            open_page("/account/login")
            for name in ("Deutschland", "Oesterreich", "Schweiz"):
                label = "Österreich" if name == "Oesterreich" else name
                select = Select(visible("#billingAddressAddressCountry"))
                select.select_by_visible_text(label)
                wait.until(lambda d: Select(d.find_element(By.ID, "billingAddressAddressCountry")).first_selected_option.text.strip() == label)
            return "DE, AT and CH selectable; no tax or shipping total assertion"
        check("Country selection", countries)

        def states():
            open_page("/account/login")
            Select(visible("#billingAddressAddressCountry")).select_by_visible_text("Deutschland")
            options = Select(visible("#billingAddressAddressCountryState")).options
            counts = collections.Counter(o.text.strip() for o in options if o.get_attribute("value"))
            require(len(counts) == 16, "Expected 16 distinct German states")
            require(not any(n > 1 for n in counts.values()), "Duplicate German state options")
        check("German state duplicates", states)

        def recovery():
            open_page("/account/login")
            click('a[href$="/account/recover"]')
            operation["name"] = "Recovery URL after link click"
            wait.until(EC.url_contains("/account/recover"))
            visible('input[type="email"]')
            driver.back()
            try:
                visible("#loginMail")
            except TimeoutException:
                state = driver.execute_script("return {path:location.pathname,ready:document.readyState,login:!!document.querySelector('#loginMail')}")
                path = state["path"] if state["path"] in ("/account/login", "/account/recover", "/") else "other public path"
                operation["name"] = "Back navigation: " + path + "; ready=" + str(state["ready"]) + "; login control exists=" + str(state["login"])
                raise
            return "Recovery page and back navigation; no email requested"
        check("Password recovery navigation", recovery)

        def page(path, heading=None):
            open_page(path)
            require(bool(visible("#content-main").text.strip()), "Main content empty")
            if heading:
                require(heading in driver.find_element(By.ID, "content-main").text.lower(), "Expected page content missing")
        check("Homepage content", lambda: page("/"))
        check("Cart page", lambda: page("/checkout/cart", "warenkorb"))
        check("Contact page", lambda: page("/kontakt/"))

        def catalog():
            open_page("/wohnen/")
            click("a.product-name")
            require(bool(visible("h1.product-detail-name").text.strip()), "Product name missing")
            visible(".product-detail-price")
            return "Listing, product navigation and price visible; no cart mutation"
        check("Listing and product detail", catalog)

        def layout():
            open_page("/account/login")
            if TARGET in ("iphone", "ipad", "android-phone", "android-tablet"):
                views = ("PORTRAIT", "LANDSCAPE")
            else:
                views = (1440, 800)
            for view in views:
                if isinstance(view, str):
                    driver.orientation = view
                else:
                    driver.set_window_size(view, 1000)
                visible("#loginMail")
                dims = driver.execute_script("return {w:innerWidth,s:document.documentElement.scrollWidth}")
                require(dims["s"] <= dims["w"] + 4, "Horizontal page overflow")
            return "Viewport overflow check; visual review remains separate"
        check("Responsive form layout", layout)
    except Exception as exc:
        REPORT["checks"].append({"name": "Browser session", "status": "BLOCKED", "detail": type(exc).__name__ + "; browser could not complete setup"})
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                REPORT["checks"].append({"name": "Session cleanup", "status": "BLOCKED", "detail": "Driver shutdown failed"})
        write_report()
    return outcome(REPORT["checks"])


if __name__ == "__main__":
    sys.exit(run())
