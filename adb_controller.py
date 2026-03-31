"""
adb_controller.py
All input and screenshots go through ADB now that BlueStacks
has Android Debug Bridge enabled in Settings → Advanced.
"""

import subprocess
import time
import random
import os
import config

TARGET = f"{config.ADB_HOST}:{config.ADB_PORT}"


def _shell(cmd: str) -> subprocess.CompletedProcess:
    """Run a shell command on the device."""
    return subprocess.run(
        ["adb", "-s", TARGET, "shell", cmd],
        capture_output=True,
        timeout=10,
    )


def connect() -> bool:
    """Connect to the emulator via ADB. Returns True on success."""
    result = subprocess.run(["adb", "connect", TARGET], capture_output=True)
    output = result.stdout.decode(errors="replace")
    print(f"[ADB] {output.strip()}")
    return "connected" in output or "already connected" in output


def screenshot(path: str = config.SCREENSHOT_PATH) -> str:
    """Capture a screenshot from the emulator and save it to *path*."""
    with open(path, "wb") as f:
        result = subprocess.run(
            ["adb", "-s", TARGET, "exec-out", "screencap", "-p"],
            stdout=f,
            stderr=subprocess.PIPE,
        )
    if result.returncode != 0:
        err = result.stderr.decode(errors="replace").strip()
        print(f"[ADB] Screenshot failed: {err}")
    elif os.path.getsize(path) < 100:
        print("[ADB] Screenshot appears empty — is the emulator running?")
    return path


def tap(x: int, y: int) -> None:
    """Tap screen at (x, y) with a randomised delay afterwards."""
    _shell(f"input tap {x} {y}")
    jitter = random.uniform(-config.TAP_JITTER, config.TAP_JITTER)
    time.sleep(config.TAP_DELAY_BASE + jitter)


def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 600) -> None:
    """Swipe from (x1, y1) to (x2, y2) over *duration_ms* milliseconds."""
    _shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
    time.sleep(0.5)


def key_back() -> None:
    """Press the Android back button."""
    _shell("input keyevent 4")
    time.sleep(0.3)
