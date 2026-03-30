"""
adb_controller.py
Thin wrapper around ADB for screen capture and touch injection.
"""

import subprocess
import threading
import time
import random
import os
import config


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        err = result.stderr.decode(errors="replace").strip()
        if err:
            print(f"[ADB] Warning: {err}")
    return result


def connect() -> bool:
    """Connect to the emulator via ADB. Returns True on success."""
    target = f"{config.ADB_HOST}:{config.ADB_PORT}"
    result = _run(["adb", "connect", target])
    output = result.stdout.decode(errors="replace")
    print(f"[ADB] {output.strip()}")
    return "connected" in output or "already connected" in output


def screenshot(path: str = config.SCREENSHOT_PATH) -> str:
    """Capture a screenshot from the emulator and save it to *path*."""
    with open(path, "wb") as f:
        result = subprocess.run(
            ["adb", "exec-out", "screencap", "-p"],
            stdout=f,
            stderr=subprocess.PIPE,
        )

    if result.returncode != 0:
        err = result.stderr.decode(errors="replace").strip()
        print(f"[ADB] Screenshot failed: {err}")
        return path

    # Validate that we actually got an image (non-empty file)
    if os.path.getsize(path) < 100:
        print("[ADB] Screenshot appears empty — is the emulator running?")

    return path


def tap(x: int, y: int) -> None:
    """Tap screen at (x, y) with a randomised delay afterwards."""
    _run(["adb", "shell", "input", "tap", str(x), str(y)])
    jitter = random.uniform(-config.TAP_JITTER, config.TAP_JITTER)
    time.sleep(config.TAP_DELAY_BASE + jitter)


def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
    """Swipe from (x1, y1) to (x2, y2) over *duration_ms* milliseconds."""
    _run(["adb", "shell", "input", "swipe",
          str(x1), str(y1), str(x2), str(y2), str(duration_ms)])
    time.sleep(0.3)


def key_back() -> None:
    """Press the Android back button."""
    _run(["adb", "shell", "input", "keyevent", "4"])
    time.sleep(0.3)


def pinch_out(cx: int = 700, cy: int = 400, spread: int = 300, duration_ms: int = 800) -> None:
    """
    Zoom out by spreading two fingers from the centre of the screen.
    Runs both swipes in parallel threads so they happen simultaneously.
    cx/cy is the centre point; spread is how far each finger travels.
    """
    def _swipe(x1, y1, x2, y2):
        subprocess.run(
            ["adb", "shell", "input", "touchscreen", "swipe",
             str(x1), str(y1), str(x2), str(y2), str(duration_ms)],
            capture_output=True,
        )

    t1 = threading.Thread(target=_swipe, args=(cx, cy, cx - spread, cy))
    t2 = threading.Thread(target=_swipe, args=(cx, cy, cx + spread, cy))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    time.sleep(0.5)
