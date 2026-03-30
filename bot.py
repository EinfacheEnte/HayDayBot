"""
bot.py
Hay Day wheat bot — plants wheat in empty plots and harvests when ready.

State machine:
  SCAN  →  HARVEST (if crops ready)
        →  PLANT   (if empty plots)
        →  WAIT    (if nothing to do)
  HARVEST  →  SCAN
  PLANT    →  WAIT
  WAIT     →  SCAN
"""

import os
import time
import sys
import adb_controller as adb
import vision
import config

# Required template files the bot needs to function
REQUIRED_TEMPLATES = [
    "empty_plot.png",    # bare unplanted field tile
    "ready_crop.png",    # sparkle/glow on a harvestable crop
    "wheat_icon.png",    # wheat in the crop selection menu
    "harvest_icon.png",  # scythe/harvest-all button
]

# Max stuck passes before giving up on a state
MAX_ATTEMPTS = 5


# ── Helpers ───────────────────────────────────────────────────────────────────

def grab() -> str:
    """Take a fresh screenshot and return its path."""
    return adb.screenshot()


def wait_for(template: str, timeout: float = config.ACTION_TIMEOUT) -> tuple[int, int] | None:
    """Poll until *template* appears or *timeout* seconds elapse."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        loc = vision.find_one(grab(), template)
        if loc:
            return loc
        time.sleep(0.5)
    return None


def check_templates() -> bool:
    """Verify all required template images exist. Returns False if any are missing."""
    missing = []
    for name in REQUIRED_TEMPLATES:
        path = os.path.join(config.TEMPLATES_DIR, name)
        if not os.path.isfile(path):
            missing.append(name)

    if missing:
        print("[BOT] Missing template images:")
        for name in missing:
            print(f"       - templates/{name}")
        print("[BOT] Capture these from the emulator before running.")
        print("[BOT] See README.md for instructions.")
        return False

    return True


# ── States ────────────────────────────────────────────────────────────────────

def state_scan() -> str:
    """
    Look for ready-to-harvest crops first, then empty plots.
    Returns 'harvest', 'plant', or 'wait'.
    """
    print("[SCAN] Taking screenshot...")
    screen = grab()

    ready = vision.find_all(screen, "ready_crop.png")
    if ready:
        print(f"[SCAN] {len(ready)} crop(s) ready to harvest.")
        return "harvest"

    empty = vision.find_all(screen, "empty_plot.png")
    if empty:
        print(f"[SCAN] {len(empty)} empty plot(s) found — time to plant.")
        return "plant"

    print("[SCAN] Nothing to do right now.")
    return "wait"


def state_harvest() -> str:
    """
    Tap the harvest-all scythe icon if visible, otherwise tap crops one by one.
    """
    # Try the harvest-all button first (fastest)
    scythe = wait_for("harvest_icon.png", timeout=3)
    if scythe:
        print(f"[HARVEST] Tapping harvest-all icon at {scythe}")
        adb.tap(*scythe)
        time.sleep(1.0)  # wait for animation
        return "scan"

    # Fall back to tapping each ready crop individually
    print("[HARVEST] No harvest-all icon — tapping crops one by one.")
    attempts = 0
    last_count = None

    while attempts < MAX_ATTEMPTS:
        screen = grab()
        crops = vision.find_all(screen, "ready_crop.png")

        if not crops:
            print("[HARVEST] All crops harvested.")
            return "scan"

        if len(crops) == last_count:
            attempts += 1
            print(f"[HARVEST] Count unchanged ({len(crops)}), attempt {attempts}/{MAX_ATTEMPTS}")
        else:
            attempts = 0

        last_count = len(crops)

        for (x, y) in crops:
            print(f"[HARVEST] Tapping crop at ({x}, {y})")
            adb.tap(x, y)
            time.sleep(0.3)

    print(f"[HARVEST] Could not harvest all crops after {MAX_ATTEMPTS} attempts. Moving on.")
    return "scan"


def state_plant() -> str:
    """
    Tap each empty plot and select wheat from the crop menu.
    """
    attempts = 0
    last_count = None

    while attempts < MAX_ATTEMPTS:
        screen = grab()
        empty_plots = vision.find_all(screen, "empty_plot.png")

        if not empty_plots:
            print("[PLANT] All plots planted.")
            return "wait"

        if len(empty_plots) == last_count:
            attempts += 1
            print(f"[PLANT] Plot count unchanged ({len(empty_plots)}), attempt {attempts}/{MAX_ATTEMPTS}")
        else:
            attempts = 0

        last_count = len(empty_plots)

        for (x, y) in empty_plots:
            print(f"[PLANT] Tapping empty plot at ({x}, {y})")
            adb.tap(x, y)
            time.sleep(config.PLANT_DELAY)  # wait for crop menu

            wheat = wait_for("wheat_icon.png", timeout=3)
            if wheat:
                print(f"[PLANT] Selecting wheat at {wheat}")
                adb.tap(*wheat)
                time.sleep(0.5)
            else:
                print("[PLANT] Crop menu didn't appear — skipping this plot.")
                adb.key_back()

    print(f"[PLANT] Could not plant all plots after {MAX_ATTEMPTS} attempts. Moving on.")
    return "wait"


def state_wait() -> str:
    """Sleep for the wheat grow time, then scan again."""
    print(f"[WAIT] Wheat grows in {config.CROP_GROW_TIME}s — sleeping...")
    time.sleep(config.CROP_GROW_TIME)
    return "scan"


# ── Main loop ─────────────────────────────────────────────────────────────────

STATE_MAP = {
    "scan":    state_scan,
    "harvest": state_harvest,
    "plant":   state_plant,
    "wait":    state_wait,
}


def run() -> None:
    if not check_templates():
        sys.exit(1)

    print("[BOT] Connecting to emulator...")
    if not adb.connect():
        print("[BOT] Could not connect to ADB. Is the emulator running?")
        sys.exit(1)

    state = "scan"
    try:
        while True:
            fn = STATE_MAP.get(state)
            if fn is None:
                print(f"[BOT] Unknown state: {state}")
                break
            state = fn()
    except KeyboardInterrupt:
        print("\n[BOT] Stopped by user.")


if __name__ == "__main__":
    run()
