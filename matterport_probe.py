"""Read-only first-stage public tour evidence; never claims tour acceptance."""
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

URL = 'https://my.matterport.com/show/?m=Q7ZYcX86N3T&play=1&qs=1'
OUTPUT = Path('matterport-evidence')
# A disposable canvas tests WebGL2 independently of Matterport's renderer.
WEBGL2 = r"""
const c=document.createElement('canvas'); c.width=4; c.height=4;
const g=c.getContext('webgl2');
if (!g) return {context:false, readback:false};
g.clearColor(0.25,0.5,0.75,1); g.clear(g.COLOR_BUFFER_BIT);
const p=new Uint8Array(4); g.readPixels(0,0,1,1,g.RGBA,g.UNSIGNED_BYTE,p);
const result={context:true, readback:Math.abs(p[0]-64)<=2 &&
 Math.abs(p[1]-128)<=2 && Math.abs(p[2]-191)<=2 && p[3]===255,
 version:g.getParameter(g.VERSION)};
const ext=g.getExtension('WEBGL_lose_context'); if(ext) ext.loseContext();
return result;
"""
INVENTORY = r"""
const visible=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);
 return r.width>0&&r.height>0&&r.right>0&&r.bottom>0&&r.left<innerWidth&&
 r.top<innerHeight&&s.display!=='none'&&s.visibility==='visible'&&s.opacity!=='0'};
return {controls:Array.from(document.querySelectorAll('button,[role="button"]'))
 .filter(visible).slice(0,60).map(e=>({tag:e.tagName,
 label:(e.getAttribute('aria-label')||e.innerText||e.getAttribute('title')||'').trim().slice(0,160),
 disabled:!!e.disabled})),
 canvases:Array.from(document.querySelectorAll('canvas')).filter(visible)
 .map(e=>({width:e.width,height:e.height})),
 iframe_count:document.querySelectorAll('iframe').length};
"""

# Inspect only rendered UI; do not read hidden application state or SDK objects.
INTERACTION_GATE = r"""
const text=(document.body?.innerText||'').toLowerCase();
const error=['browser not supported','browser nicht unterstützt','webgl requires',
 'webgl erfordert','access denied','verify you are human','checking your browser',
 'captcha','just a moment','not available','nicht verfügbar'].some(s=>text.includes(s));
const large=Array.from(document.querySelectorAll('canvas')).some(e=>{
 const r=e.getBoundingClientRect(),s=getComputedStyle(e);
 return e.width>0&&e.height>0&&r.width>=640&&r.height>=360&&
 s.display!=='none'&&s.visibility==='visible'&&s.opacity!=='0'&&
 Math.min(r.right,innerWidth)-Math.max(r.left,0)>=640&&
 Math.min(r.bottom,innerHeight)-Math.max(r.top,0)>=360;
});
const active=document.activeElement;
return {recognized_error:error, large_visible_canvas:large,
 editable_focus:!!active&&(active.matches('input,textarea,select')||active.isContentEditable)};
"""


def may_interact(webgl, capture, gate):
    return (webgl == 'PASS' and capture is True and
            gate.get('recognized_error') is False and
            gate.get('large_visible_canvas') is True and
            gate.get('editable_focus') is False)


def allowed(env):
    return (env.get('GITHUB_ACTIONS') == 'true' and
            env.get('GITHUB_REPOSITORY') == 'badartshoptest/badart-browser-checks' and
            env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and
            env.get('GITHUB_REF') == 'refs/heads/main' and
            env.get('CONFIRMED_RUN') == 'true' and
            env.get('REPOSITORY_PUBLIC') == 'true' and
            env.get('REPOSITORY_FORK') == 'false')


def expected_url(url):
    parsed = urlsplit(url)
    return (parsed.scheme == 'https' and parsed.netloc == 'my.matterport.com' and
            parsed.path == '/show/' and parse_qs(parsed.query).get('m') == ['Q7ZYcX86N3T'])


def new_report():
    return {'started_utc': datetime.now(timezone.utc).isoformat(), 'tour': URL,
            'scope': 'Candidate keyboard movement/rotation; visual review required.',
            'actions': [],
            'webgl2': 'NOT VERIFIED', 'interior_rendered': 'NOT VERIFIED',
            'movement_between_stations': 'NOT VERIFIED',
            'overall': 'NOT VERIFIED', 'snapshots': [], 'errors': []}


def outcome(report):
    # No first-stage run may be mistaken for a fully verified showroom visit.
    return 1 if report['errors'] or report['webgl2'] == 'FAIL' else 2


def emit(report, capture):
    report['finished_utc'] = datetime.now(timezone.utc).isoformat()
    report['exit_code'] = outcome(report)
    # Untrusted page labels never go to public logs/Markdown summaries.
    summary = ('Matterport feasibility probe: NOT VERIFIED\n'
               f"WebGL2 disposable-canvas draw/readback: {report['webgl2']}\n"
               'Rendered interior: NOT VERIFIED (manual screenshot review required)\n'
               'Movement between two real stations: NOT VERIFIED (candidate actions are not proof)\n'
               f"Candidate key actions attempted: {len(report['actions'])}\n"
               f"Evidence snapshots collected: {len(report['snapshots'])}\n"
               f"Operational errors: {len(report['errors'])}\n"
               'A failed/incomplete Actions conclusion is intentional, not acceptance.\n')
    print(summary)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write(summary)
    if capture:
        OUTPUT.mkdir(exist_ok=True)
        (OUTPUT / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')


def run():
    if not allowed(os.environ):
        print('Refused: manually confirmed public original-repository main-branch run required.')
        return 1
    capture = os.environ.get('CAPTURE_EVIDENCE') == 'true'
    report = new_report()
    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait
        browser = os.environ.get('PROBE_BROWSER', '')
        if browser not in ('chrome', 'firefox'):
            raise ValueError('UnsupportedBrowser')
        report['requested_browser'] = browser
        options = webdriver.ChromeOptions() if browser == 'chrome' else webdriver.FirefoxOptions()
        options.add_argument('--headless=new' if browser == 'chrome' else '-headless')
        # No sandbox bypass, web-security override or unsafe software rendering.
        driver = (webdriver.Chrome if browser == 'chrome' else webdriver.Firefox)(options=options)
        driver.set_window_size(1440, 1000)
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(15)
        report['environment'] = {k: driver.capabilities.get(k) for k in
                                 ('browserName', 'browserVersion', 'platformName')}
        report['environment']['runner_os'] = platform.platform()
        driver.get(URL)
        if not expected_url(driver.current_url):
            raise RuntimeError('UnexpectedDestination')
        WebDriverWait(driver, 30).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        gl = driver.execute_script(WEBGL2)
        report['webgl2_evidence'] = gl
        report['webgl2'] = 'PASS' if gl.get('context') is True and gl.get('readback') is True else 'FAIL'
        def observe(name):
            if not expected_url(driver.current_url):
                raise RuntimeError('UnexpectedDestination')
            snapshot = {'name': name, 'observed_utc': datetime.now(timezone.utc).isoformat()}
            if capture:
                snapshot['visible_inventory'] = driver.execute_script(INVENTORY)
                OUTPUT.mkdir(exist_ok=True)
                filename = name + '.png'
                if not driver.save_screenshot(str(OUTPUT / filename)):
                    raise RuntimeError('ScreenshotFailed')
                snapshot['screenshot'] = filename
            report['snapshots'].append(snapshot)

        time.sleep(30)
        observe('initial')
        # Only the documented navigation keys. A canvas gate is NOT room proof.
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys
        for name, key in [('candidate-forward', Keys.ARROW_UP),
                          ('candidate-rotate', 'j'),
                          ('candidate-forward-2', Keys.ARROW_UP)]:
            if not expected_url(driver.current_url):
                raise RuntimeError('UnexpectedDestination')
            gate = driver.execute_script(INTERACTION_GATE)
            report.setdefault('interaction_gates', []).append(gate)
            if not may_interact(report['webgl2'], capture, gate):
                report['interaction_stop'] = 'WebGL2, capture approval, visible canvas or safety gate missing'
                break
            report['actions'].append({'name': name, 'status': 'ATTEMPTED, NOT VERIFIED'})
            if key == 'j':
                ActionChains(driver).key_down(key).pause(0.8).key_up(key).perform()
            else:
                ActionChains(driver).send_keys(key).perform()
            time.sleep(8)
            observe(name)
    except Exception as exc:
        # No raw exception, HTML, URLs, headers, cookies or storage contents in logs.
        report['errors'].append({'stage': 'probe', 'type': type(exc).__name__})
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception as exc:
                report['errors'].append({'stage': 'cleanup', 'type': type(exc).__name__})
        emit(report, capture)
    return outcome(report)


if __name__ == '__main__':
    sys.exit(run())
