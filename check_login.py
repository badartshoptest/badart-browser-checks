"""Opt-in login acceptance. Credentials come only from private CI secrets.

No registration, reset email, address mutation, cart mutation or order submission.
Never output account page text, screenshots, credentials or exception messages.
"""
import os
import platform
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from check_shop import BASE, TARGET, create_driver, safe_text
from pathlib import Path


def report(*parts):
    message = ' '.join(map(str, parts))
    print(message)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a', encoding='utf-8') as stream:
            stream.write(message + '\n\n')


def run():
    email = os.environ.get('SHOP_TEST_EMAIL')
    password = os.environ.get('SHOP_TEST_PASSWORD')
    if not email or not password:
        report('BLOCKED: Dedicated test-account secrets are not configured.')
        return 2
    driver = None
    try:
        driver = create_driver()
        wait = WebDriverWait(driver, 30)
        driver.set_page_load_timeout(60)
        driver.get(BASE + '/account/login')
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        body = driver.find_element(By.TAG_NAME, 'body').text.lower()
        if any(s in body for s in ('verify you are human', 'checking your browser', 'access denied', 'just a moment')):
            report('BLOCKED: Site security challenge; no credential submission.')
            return 2
        for button in driver.find_elements(By.CSS_SELECTOR, 'button'):
            if button.is_displayed() and button.text.strip() in ('Nur notwendige', 'Nur technisch notwendige', 'Nur technisch notwendige Cookies', 'Ablehnen'):
                button.click()
                break
        mail = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#loginMail')))
        secret = driver.find_element(By.CSS_SELECTOR, '#loginPassword')
        mail.send_keys(email)
        secret.send_keys(password)
        driver.find_element(By.CSS_SELECTOR, '#loginPassword').find_element(By.XPATH, 'ancestor::form').find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        # Positive authenticated evidence, without copying any customer content.
        wait.until(lambda d: bool(d.find_elements(By.CSS_SELECTOR, 'a[href$="/account/logout"]')))
        report('PASS: Dedicated test account authenticated; logout control exists.')
        report('Environment:', safe_text(TARGET), safe_text(driver.capabilities.get('browserVersion', 'not reported')), safe_text(platform.platform()))
        return 0
    except Exception as exc:
        report('BLOCKED: Login acceptance incomplete; diagnostic class:', type(exc).__name__)
        return 2
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == '__main__':
    raise SystemExit(run())
