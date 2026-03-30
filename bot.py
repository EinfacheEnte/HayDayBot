"""
bot.py
Hay Day weed bot — harvests all weeds on the farm and lists them for sale
in the roadside shop.

State machine:
  SCAN  →  HARVEST  →  SELL  →  WAIT  →  SCAN  → …
"""

import time
import sys
import adb_controller as adb
import vision
import config


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


# ── States ────────────────────────────────────────────────────────────────────

def state_scan() -> str:
    """
    Scan the farm for weeds.
    Returns 'harvest' if weeds found, 'sell' if inventory has weeds but none
    on farm, or 'wait' if nothing to do.
    """
    print("[SCAN] Taking screenshot...")
    weeds = vision.find_all(grab(), "weed.png")
    if weeds:
        print(f"[SCAN] Found {len(weeds)} weed(s).")
        return "harvest"
    print("[SCAN] No weeds on farm.")
    return "sell"


def state_harvest() -> str:
    """Tap every visible weed and confirm the harvest pop-up."""
    while True:
        weeds = vision.find_all(grab(), "weed.png")
        if not weeds:
            print("[HARVEST] All weeds cleared.")
            return "sell"

        for (x, y) in weeds:
            print(f"[HARVEST] Tapping weed at ({x}, {y})")
            adb.tap(x, y)

            # Wait for the harvest confirmation button to appear
            btn = wait_for("harvest_btn.png")
            if btn:
                print(f"[HARVEST] Confirming harvest at {btn}")
                adb.tap(*btn)
            else:
                print("[HARVEST] No harvest button appeared — skipping.")


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

        # Confirm the price (accept game's default minimum)
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
