"""
adb_controller.py
- Screenshots: ADB exec-out (the only ADB command that works on BlueStacks)
- All input (tap, swipe, key): pyautogui clicking on the BlueStacks window
"""

import subprocess
import time
import random
import os
import pyautogui
import config

# Disable pyautogui's fail-safe (moving mouse to corner stops the bot)
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0  # we handle our own delays


# ── ADB (screenshots only) ────────────────────────────────────────────────────

def connect() -> bool:
    """Connect to the emulator via ADB. Returns True on success."""
    target = f"{config.ADB_HOST}:{config.ADB_PORT}"
    result = subprocess.run(["adb", "connect", target], capture_output=True)
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
    elif os.path.getsize(path) < 100:
        print("[ADB] Screenshot appears empty — is the emulator running?")
    return path


# ── Window detection ──────────────────────────────────────────────────────────

_window_cache: tuple[int, int, int, int] | None = None


def _get_game_area() -> tuple[int, int, int, int]:
    """
    Return the (x, y, w, h) of the BlueStacks game area on the Mac screen.
    Uses osascript bounds (left, top, right, bottom) of the largest BlueStacks
    window. Falls back to full screen if detection fails or looks wrong.
    """
    global _window_cache
    if _window_cache:
        return _window_cache

    # Use 'bounds' which returns left, top, right, bottom — more reliable than
    # position+size which can behave oddly on Retina / fullscreen windows.
    script = """
    tell application "System Events"
        set proc to first process whose name contains "BlueStacks"
        set wins to windows of proc
        set bestBounds to {0, 0, 0, 0}
        set bestArea to 0
        repeat with w in wins
            try
                set b to bounds of w
                set area to (item 3 of b - item 1 of b) * (item 4 of b - item 2 of b)
                if area > bestArea then
                    set bestArea to area
                    set bestBounds to b
                end if
            end try
        end repeat
        return (item 1 of bestBounds as text) & "," & (item 2 of bestBounds as text) & "," & (item 3 of bestBounds as text) & "," & (item 4 of bestBounds as text)
    end tell
    """
    raw = ""
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
        raw = result.stdout.strip()
        parts = [p.strip() for p in raw.split(",")]
        left, top, right, bottom = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
        ww = right - left
        wh = bottom - top
        print(f"[INPUT] osascript raw bounds: left={left} top={top} right={right} bottom={bottom} → w={ww} h={wh}")
    except Exception as e:
        print(f"[INPUT] osascript failed ({e}) — falling back to full screen")
        ww, wh = pyautogui.size()
        left, top = 0, 0

    # Sanity check — if height is tiny the detection went wrong
    if wh < 200:
        sw, sh = pyautogui.size()
        print(f"[INPUT] Window h={wh} looks wrong — using full screen size {sw}x{sh}")
        left, top, ww, wh = 0, 0, sw, sh

    # Subtract toolbar so (0,0) maps to top-left of the actual game image
    game_y = top + config.BLUESTACKS_TOOLBAR_HEIGHT
    game_h = wh - config.BLUESTACKS_TOOLBAR_HEIGHT

    _window_cache = (left, game_y, ww, game_h)
    print(f"[INPUT] Game area: x={left} y={game_y} w={ww} h={game_h}")
    return _window_cache


def _game_to_screen(gx: int, gy: int) -> tuple[int, int]:
    """Map game coordinates (2560x1440) to Mac screen coordinates."""
    ax, ay, aw, ah = _get_game_area()
    sx = ax + int(gx / config.GAME_W * aw)
    sy = ay + int(gy / config.GAME_H * ah)
    return sx, sy


# ── Input (pyautogui) ─────────────────────────────────────────────────────────

def tap(x: int, y: int) -> None:
    """Tap game coordinate (x, y) by clicking on the BlueStacks window."""
    sx, sy = _game_to_screen(x, y)
    pyautogui.click(sx, sy)
    jitter = random.uniform(-config.TAP_JITTER, config.TAP_JITTER)
    time.sleep(config.TAP_DELAY_BASE + jitter)


def swipe(x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
    """Swipe between two game coordinates."""
    sx1, sy1 = _game_to_screen(x1, y1)
    sx2, sy2 = _game_to_screen(x2, y2)
    pyautogui.moveTo(sx1, sy1)
    pyautogui.dragTo(sx2, sy2, duration=duration_ms / 1000, button="left")
    time.sleep(0.3)


def key_back() -> None:
    """Press Escape as the Android back button equivalent in BlueStacks."""
    pyautogui.press("escape")
    time.sleep(0.3)
