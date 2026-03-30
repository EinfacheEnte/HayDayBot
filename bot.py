"""
bot.py
Hay Day weed bot — harvests all weeds on the farm and lists them for sale
in the roadside shop.

State machine:
  SCAN  →  HARVEST  →  SELL  →  WAIT  →  SCAN  → …
"""

import os
import time
import sys
import adb_controller as adb
import vision
import config

# Required template files the bot needs to function
REQUIRED_TEMPLATES = [
    "weed.png",
    "harvest_btn.png",
    "shop_icon.png",
    "sell_btn.png",
    "price_confirm.png",
]

# Max times to attempt harvesting the same set of weeds before giving up
MAX_HARVEST_ATTEMPTS = 5


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
    Scan the farm for weeds.
    Returns 'harvest' if weeds found, or 'wait' if nothing to do.
    """
    print("[SCAN] Taking screenshot...")
    weeds = vision.find_all(grab(), "weed.png")
    if weeds:
        print(f"[SCAN] Found {len(weeds)} weed(s).")
        return "harvest"
    print("[SCAN] No weeds on farm.")
    return "wait"


def state_harvest() -> str:
    """Tap every visible weed and confirm the harvest pop-up."""
    attempts = 0
    last_count = None

    while attempts < MAX_HARVEST_ATTEMPTS:
        weeds = vision.find_all(grab(), "weed.png")
        if not weeds:
            print("[HARVEST] All weeds cleared.")
            return "sell"

        # If weed count hasn't changed after a full pass, something is wrong
        if weeds and len(weeds) == last_count:
            attempts += 1
            print(f"[HARVEST] Weed count unchanged ({len(weeds)}), attempt {attempts}/{MAX_HARVEST_ATTEMPTS}")
        else:
            attempts = 0  # progress was made, reset counter

        last_count = len(weeds)

        for (x, y) in weeds:
            print(f"[HARVEST] Tapping weed at ({x}, {y})")
            adb.tap(x, y)

            btn = wait_for("harvest_btn.png")
            if btn:
                print(f"[HARVEST] Confirming harvest at {btn}")
                adb.tap(*btn)
            else:
                print("[HARVEST] No harvest button appeared — skipping.")

    print(f"[HARVEST] Could not clear all weeds after {MAX_HARVEST_ATTEMPTS} attempts. Moving on.")
    return "sell"


def state_sell() -> str:
    """Navigate to the roadside shop and list weeds for sale."""
    print("[SELL] Navigating to roadside shop...")
    shop = wait_for("shop_icon.png")
    if not shop:
        print("[SELL] Could not find shop — will retry next cycle.")
        return "wait"

    adb.tap(*shop)
    time.sleep(1.5)  # wait for shop to open

    # List weeds until no sell slot is available
    listed = 0
    while True:
        sell_btn = wait_for("sell_btn.png", timeout=3)
        if not sell_btn:
            print(f"[SELL] No more sell slots. Listed {listed} item(s).")
            break

        adb.tap(*sell_btn)
        time.sleep(0.8)

        confirm = wait_for("price_confirm.png", timeout=3)
        if confirm:
            adb.tap(*confirm)
            time.sleep(config.SELL_WAIT)
            listed += 1
        else:
            print("[SELL] Price confirm not found — backing out.")
            adb.key_back()
            break

    adb.key_back()  # close shop
    return "wait"


def state_wait() -> str:
    print(f"[WAIT] Sleeping {config.SCAN_INTERVAL}s before next scan...")
    time.sleep(config.SCAN_INTERVAL)
    return "scan"


# ── Main loop ─────────────────────────────────────────────────────────────────

STATE_MAP = {
    "scan":    state_scan,
    "harvest": state_harvest,
    "sell":    state_sell,
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
