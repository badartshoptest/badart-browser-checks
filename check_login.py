"""Opt-in login acceptance. Credentials come only from private CI secrets.

No registration, reset email, address mutation, cart mutation or order submission.
Never output account page text, screenshots, credentials or exception messages.
"""
import os
import platform
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from check_shop import BASE, TARGET, CONSENT, create_driver, safe_text
from pathlib import Path
from urllib.parse import urlsplit


def login_state(driver):
    text = driver.find_element(By.TAG_NAME, 'body').text.lower()
    if 'kein account mit den angegebenen zugangsdaten' in text:
        return 'rejected'
    path = urlsplit(driver.current_url).path
    origin = urlsplit(driver.current_url).hostname
    if origin not in ('www.badart-shop.de', 'badart-shop.de'):
        return 'unexpected_origin'
    # A protected URL alone can also render an error or an unfinished page.
    overview = 'hier haben sie direkten zugriff auf ihre profilinformationen' in text
    if path in ('/account', '/account/') and overview and not driver.find_elements(By.CSS_SELECTOR, '#loginMail'):
        return 'authenticated'
    if driver.find_elements(By.CSS_SELECTOR, 'a[href*="/account/logout"]'):
        return 'authenticated'
    return False


def report(*parts):
    message = ' '.join(map(str, parts))
    print(message, flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a', encoding='utf-8') as stream:
            stream.write(message + '\n\n')


def login_controls(driver):
    """At most one read-only page reload, always before any credential entry."""
    wait = WebDriverWait(driver, 30, ignored_exceptions=(StaleElementReferenceException,))
    for attempt in range(2):
        destination = urlsplit(driver.current_url)
        if destination.scheme != 'https' or destination.hostname not in ('www.badart-shop.de', 'badart-shop.de'):
            raise RuntimeError('Unexpected credential destination')
        try:
            mail = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#loginMail')))
            secret = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#loginPassword')))
            return mail, secret
        except TimeoutException:
            path = destination.path
            report('Pre-entry route:', path if path in ('/account/login', '/account/logout') else 'other route')
            report('Pre-entry login controls present:', bool(driver.find_elements(By.CSS_SELECTOR, '#loginMail')))
            # Only public structural metadata, before any credential has been entered.
            report('Pre-entry page title:', safe_text(driver.title))
            inputs = driver.execute_script("return Array.from(document.querySelectorAll('input')).slice(0,35).map(e=>[e.id,e.name,e.type].join(':'))")
            report('Pre-entry input identities:', safe_text(', '.join(inputs)))
            if '403 forbidden' in str(driver.title).lower():
                report('BLOCKED: Shop returned 403 Forbidden to this test browser; no credentials submitted and no further retry.')
                raise RuntimeError('Shop access denied')
            body = driver.find_element(By.TAG_NAME, 'body').text.lower()
            if any(s in body for s in ('verify you are human', 'checking your browser', 'access denied', 'just a moment')):
                report('BLOCKED: Site security challenge; no credential submission or further retry.')
                raise RuntimeError('Site security challenge')
            if attempt or destination.path != '/account/login':
                raise
            report('RETRY: Login controls unavailable on initial visit; one read-only reload before credential entry.')
            driver.get(BASE + '/account/login')
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
    raise RuntimeError('Login controls unavailable')


def run():
    email = os.environ.get('SHOP_TEST_EMAIL')
    password = os.environ.get('SHOP_TEST_PASSWORD')
    if not email or not password:
        report('BLOCKED: Dedicated test-account secrets are not configured.')
        return 2
    driver = None
    stage = 'browser startup'
    try:
        report('INFO: Starting browser environment.')
        driver = create_driver()
        report('INFO: Browser environment connected.')
        wait = WebDriverWait(driver, 30, ignored_exceptions=(StaleElementReferenceException,))
        driver.set_page_load_timeout(60)
        stage = 'login page'
        driver.get(BASE + '/account/login')
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        # Atomic page read avoids a stale body handle during storefront hydration.
        body = wait.until(lambda d: d.execute_script('return document.body ? document.body.innerText : null')).lower()
        if '403 forbidden' in str(driver.title).lower():
            report('BLOCKED: Shop returned 403 Forbidden to this test browser; no credential submission.')
            return 2
        if any(s in body for s in ('verify you are human', 'checking your browser', 'access denied', 'just a moment')):
            report('BLOCKED: Site security challenge; no credential submission.')
            return 2
        wanted = ['Alle akzeptieren', 'Alle Cookies akzeptieren'] if CONSENT == 'all' else ['Nur notwendige', 'Nur technisch notwendige', 'Nur technisch notwendige Cookies', 'Ablehnen']
        def consent_ready(d):
            button = d.execute_script("return Array.from(document.querySelectorAll('button, a.btn')).find(e=>e.getClientRects().length && arguments[0].includes(e.innerText.trim())) || null", wanted)
            if button is not None:
                button.click()
            return True
        wait.until(consent_ready)
        destination = urlsplit(driver.current_url)
        if destination.scheme != 'https' or destination.hostname not in ('www.badart-shop.de', 'badart-shop.de'):
            report('BLOCKED: Credential entry requires the authorized HTTPS shop origin.')
            return 2
        stage = 'login controls'
        mail, secret = login_controls(driver)
        report('INFO: Login controls available before credential entry.')
        destination = urlsplit(driver.current_url)
        if destination.scheme != 'https' or destination.hostname not in ('www.badart-shop.de', 'badart-shop.de'):
            report('BLOCKED: Credential entry requires the authorized HTTPS shop origin.')
            return 2
        mail.clear()
        secret.clear()
        mail.send_keys(email)
        secret.send_keys(password)
        if not driver.execute_script('return arguments[0].validity.valid', mail):
            report('BLOCKED: Stored test email does not pass browser email validation; no login submitted.')
            return 2
        stage = 'login result'
        submit = driver.find_element(By.CSS_SELECTOR, '#loginPassword').find_element(By.XPATH, 'ancestor::form').find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        if TARGET in ('iphone', 'ipad', 'android-phone', 'android-tablet'):
            if TARGET.startswith('android-'):
                driver.execute_script("arguments[0].scrollIntoView({block:'end',behavior:'instant'});window.scrollBy(0,80)", submit)
            else:
                driver.execute_script("arguments[0].scrollIntoView({block:'center',behavior:'instant'})", submit)
            stable = {'rect': None, 'since': time.monotonic()}
            def settled(d):
                rect = d.execute_script('const r=arguments[0].getBoundingClientRect();return [Math.round(r.x),Math.round(r.y)]', submit)
                if rect != stable['rect']:
                    stable.update(rect=rect, since=time.monotonic())
                return time.monotonic() - stable['since'] >= 0.6
            wait.until(settled)
        submit.click()
        # Positive authenticated evidence, without copying any customer content.
        state = wait.until(login_state)
        if state != 'authenticated':
            report('FAIL: Shop rejected the supplied test-account credentials.' if state == 'rejected' else 'BLOCKED: Unexpected login navigation origin.')
            return 1 if state == 'rejected' else 2
        report('PASS: Dedicated test account authenticated; protected account page or logout control confirmed.')
        report('Environment:', safe_text(TARGET), safe_text(driver.capabilities.get('browserVersion', 'not reported')), safe_text(platform.platform()))
        report('Browser platform:', safe_text(driver.capabilities.get('platformName', 'not reported')), safe_text(driver.capabilities.get('platformVersion', 'not reported')))
        return 0
    except Exception as exc:
        report('BLOCKED: Login acceptance incomplete; stage:', stage, '; diagnostic class:', type(exc).__name__)
        if driver is not None and stage == 'login result':
            try:
                path = urlsplit(driver.current_url).path
                report('Result page:', path if path in ('/account/login', '/account', '/account/', '/checkout/confirm') else 'other route')
                report('Login controls still present:', bool(driver.find_elements(By.CSS_SELECTOR, '#loginMail')))
            except Exception:
                pass
        return 2
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == '__main__':
    raise SystemExit(run())
