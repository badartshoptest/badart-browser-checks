# Separate Matterport feasibility probe

Explicit, separately approved exception to the shop suite's no-screenshot/no-artifact
policy. No changes to `check_shop.py`, `.github/workflows/browser-checks.yml`, root
README, or shop dependencies. Existing shop tests still upload no artifacts.

## Scope and approval

Only the fixed public tour https://my.matterport.com/show/?m=Q7ZYcX86N3T&play=1&qs=1
(BESTES FÜRS BAD) is opened in fresh Chrome and Firefox sessions. One manual
workflow dispatch creates two independent standard Windows-2025 jobs with an
8-minute timeout each. No credentials, secrets, SDK keys, accounts, paid runners,
schedules, arbitrary coordinate clicks or browser-security changes.
Only main in public `badartshoptest/badart-browser-checks` is eligible, not forks
or private repositories. Read-only GitHub token; checkout retains no credentials.

Run only with the repository owner's approval for the public-tour screenshots
and artifact visibility described below.

## Starting the approved run

Actions → Matterport initial feasibility probe → Run workflow, branch main.
Enable `confirmed_run` and `capture_evidence` for the approved evidence run.
Both default false. Without capture approval no screenshots or labels are saved
and no keyboard navigation occurs.

Each browser uploads report.json and up to four screenshots to its own artifact,
retained for one day. Treat artifacts as accessible to signed-in GitHub users with
read access to the public repo. Logs/summaries follow normal repository retention.
Screenshots and bounded visible button labels are untrusted website content.
No HTML dumps, body-text dumps, cookies, storage, headers or raw exceptions are
saved. Visible body text is inspected transiently for error/security phrases.
The public site receives normal runner IP/browser metadata.

## Observations and conservative interpretation

`play=1&qs=1` requests automatic opening without the dollhouse introduction.
After a 30-second observation window, take an initial screenshot. When WebGL2
works, capture is approved, a large canvas occupies at least 640 × 360 visible viewport pixels,
no recognized security/browser error appears, and no editable control is focused:

1. Send ArrowUp once, wait eight seconds, capture candidate-forward.
2. Recheck the gates, hold J for 0.8 seconds and release, wait eight seconds, capture candidate-rotate.
3. Recheck, send ArrowUp once, wait eight seconds, capture candidate-forward-2.

Keys go to the current document using Selenium ActionChains. There are no focus
changes, arbitrary clicks, tabindex modifications, overlays dismissed, or hidden
app state reads. A transparent interaction overlay does not prevent the canvas
gate. U/deep-link extraction is not implemented. Gates are conservative heuristics,
not proof of a rendered room or lack of occlusion. An unrecognized error or splash
can still exist, so key attempts and changed images never imply a verified visit.

- `webgl2: PASS`: a separate disposable canvas obtained a WebGL2 context, drew a
  known color and read it back. This does not prove Matterport rendered.
- `interior_rendered: NOT VERIFIED`: requires screenshot review. Black/blank
  canvas, loader, cover image, splash and error screens do not count as rooms.
- `movement_between_stations: NOT VERIFIED`: keyboard actions are only attempts.
  Changed images alone can be rotation/loading/animation, not a different station.
- `overall: NOT VERIFIED`: always. Exit 2 means incomplete acceptance; exit 1 means
  an operational failure or failed WebGL2 capability. The Actions job deliberately
  remains non-green, even if evidence was collected. Review reports/artifacts.

A grounded follow-up must identify actual distinct positions, ideally with visible
location links, and inspect the scene before claiming two stations were visited.
No automatic counts or success claims arise from these candidate key presses.

## Sources and local checks

Documented opening parameters:
https://support.matterport.com/s/article/How-to-Connect-Two-or-More-Spaces-with-Mattertags-and-Deep-Links?language=en_US
Documented keyboard directions (arrow keys move, I/J/K/L rotate):
https://matterport.github.io/developer-docs/reference/camera/

`python -m unittest -v test_matterport_probe`
`python -m py_compile matterport_probe.py test_matterport_probe.py`

Seven self-tests cover guards, destination validation, interaction gates,
failure/incomplete reporting and evidence opt-in. They do not launch a browser.
YAML syntax, browser matrix, trigger, permissions, SHA pins, runner, timeout and
retention were checked locally with PyYAML. Actual runner/browser startup, WebGL2,
Matterport rendering, key delivery, screenshots and uploads remain untested.

Official upload-artifact v4 ref checked through GitHub on 2026-11-08:
https://github.com/actions/upload-artifact/commit/ea165f8d65b6e75b540449e92b4886f43607fa02
Checkout/setup-python pins and Selenium 4.52.0 match the existing repository.
