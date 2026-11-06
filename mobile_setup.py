"""Start a disposable simulator/emulator and loopback-only Appium server in CI."""
import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path


def command(*args, **kwargs):
    return subprocess.check_output(args, text=True, timeout=600, **kwargs).strip()


def choose_ios(data, target, max_major=None):
    prefix = "iPhone" if target == "iphone" else "iPad"
    candidates = []
    for runtime, devices in data["devices"].items():
        if ".iOS-" not in runtime:
            continue
        version = tuple(int(n) for n in re.findall(r"\d+", runtime.split(".iOS-")[1]))
        if max_major is not None and version[0] > max_major:
            continue
        for device in devices:
            if device.get("isAvailable") and device["name"].startswith(prefix):
                candidates.append((version, device["name"], device["udid"]))
    if not candidates:
        raise RuntimeError("No compatible installed Apple simulator")
    version, name, udid = sorted(candidates)[-1]
    return {"platformName": "iOS", "browserName": "Safari", "appium:automationName": "XCUITest",
            "appium:udid": udid, "appium:deviceName": name,
            "appium:platformVersion": ".".join(map(str, version)),
            "appium:newCommandTimeout": 180, "appium:wdaLaunchTimeout": 180000,
            "appium:safariInitialUrl": "about:blank"}


def wait_for_server(process, timeout=180):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if process.poll() is not None:
            print("Appium startup diagnostics:", Path("appium.log").read_text(errors="replace")[-10000:], flush=True)
            raise RuntimeError("Appium exited before becoming ready")
        try:
            with urllib.request.urlopen("http://127.0.0.1:4723/status", timeout=3) as response:
                if json.load(response).get("value", {}).get("ready"):
                    return
        except Exception:
            pass
        time.sleep(2)
    print("Appium startup diagnostics:", Path("appium.log").read_text(errors="replace")[-10000:], flush=True)
    raise RuntimeError("Appium did not become ready")


def main():
    target = os.environ["TARGET"]
    if target in ("iphone", "ipad"):
        sdk_version = command("xcrun", "--sdk", "iphonesimulator", "--show-sdk-version")
        caps = choose_ios(json.loads(command("xcrun", "simctl", "list", "devices", "available", "--json")), target,
                          max_major=int(sdk_version.split(".")[0]))
        print("Selected Apple simulator:", caps["appium:deviceName"], caps["appium:platformVersion"], "active SDK", sdk_version, flush=True)
        subprocess.run(["xcrun", "simctl", "boot", caps["appium:udid"]], check=True, timeout=120)
        subprocess.run(["xcrun", "simctl", "bootstatus", caps["appium:udid"], "-b"], check=True, timeout=600)
        appium_args = ["appium", "--address", "127.0.0.1", "--port", "4723", "--log-level", "error"]
    else:
        sdk = Path(os.environ["ANDROID_HOME"])
        sdkmanager = str(sdk / "cmdline-tools/latest/bin/sdkmanager")
        avdmanager = str(sdk / "cmdline-tools/latest/bin/avdmanager")
        adb = str(sdk / "platform-tools/adb")
        # Recent avdmanager and emulator releases use different default user directories.
        android_user = Path.home() / ".android"
        android_user.mkdir(parents=True, exist_ok=True)
        avd_home = Path("ci-android/avd").resolve()
        avd_home.mkdir(parents=True, exist_ok=True)
        os.environ["ANDROID_USER_HOME"] = str(android_user)
        os.environ["ANDROID_EMULATOR_HOME"] = str(android_user)
        os.environ["ANDROID_AVD_HOME"] = str(avd_home)
        image = "system-images;android-35;google_apis_playstore;x86_64"
        subprocess.run([sdkmanager, "platform-tools", "emulator", image], check=True, timeout=600)
        subprocess.run([avdmanager, "create", "avd", "--name", "badart-ci", "--package", image,
                        "--device", "pixel_7", "--path", str(avd_home / "badart-ci.avd")], input="no\n", text=True, check=True, timeout=120)
        if "badart-ci" not in command(str(sdk / "emulator/emulator"), "-list-avds").splitlines():
            raise RuntimeError("Created Android device is not discoverable by the emulator")
        # Establish the standard host key before the emulator imports trusted host keys.
        subprocess.run([adb, "kill-server"], check=False, timeout=30)
        subprocess.run([adb, "start-server"], check=True, timeout=30)
        with open("emulator.log", "w") as log:
            emulator = subprocess.Popen([str(sdk / "emulator/emulator"), "-avd", "badart-ci", "-no-window",
                              "-no-audio", "-no-boot-anim", "-no-snapshot", "-gpu", "software",
                              "-memory", "3072"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        end = time.monotonic() + 240
        while True:
            if emulator.poll() is not None or time.monotonic() > end:
                # Boot-only infrastructure log: no browser session, account or shop form exists yet.
                print("Emulator startup diagnostics:", Path("emulator.log").read_text(errors="replace")[-10000:])
                raise RuntimeError("Android emulator exited or did not connect to adb")
            if "emulator-5554\tdevice" in command(adb, "devices"):
                break
            time.sleep(3)
        end = time.monotonic() + 240
        while command(adb, "shell", "getprop", "sys.boot_completed") != "1":
            if time.monotonic() > end:
                raise RuntimeError("Android emulator boot timeout")
            time.sleep(3)
        command(adb, "shell", "input", "keyevent", "82")
        if target == "android-tablet":
            command(adb, "shell", "wm", "size", "1600x2560")
            command(adb, "shell", "wm", "density", "240")
        if not command(adb, "shell", "pm", "path", "com.android.chrome"):
            raise RuntimeError("Android system image has no Chrome")
        caps = {"platformName": "Android", "browserName": "Chrome", "appium:automationName": "UiAutomator2",
                "appium:deviceName": "Android tablet viewport" if target.endswith("tablet") else "Pixel 7 emulator",
                "appium:udid": "emulator-5554", "appium:newCommandTimeout": 180,
                "appium:adbExecTimeout": 90000, "appium:chromedriverAutodownload": True,
                "appium:chromeOptions": {"args": ["--no-first-run", "--disable-fre"]}}
        appium_args = ["appium", "--address", "127.0.0.1", "--port", "4723", "--log-level", "error",
                       "--allow-insecure", "uiautomator2:chromedriver_autodownload"]
    Path("mobile-capabilities.json").write_text(json.dumps(caps), encoding="utf-8")
    with open("appium.log", "w") as log:
        appium = subprocess.Popen(appium_args, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    wait_for_server(appium)
    print("Mobile environment ready:", caps["appium:deviceName"], caps.get("appium:platformVersion", "Android 15"))


if __name__ == "__main__":
    main()
