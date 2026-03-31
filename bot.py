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
    "wheat_top.png",     # golden spiky tip of a wheat stalk (matches all rows)
    "wheat_icon.png",    # wheat in the crop selection menu
    "harvest_icon.png",  # scythe/harvest-all button
]

# Max stuck passes before giving up on a state
MAX_ATTEMPTS = 5


# ── Helpers ───────────────────────────────────────────────────────────────────

def grab() -> str:
    """Take a fresh screenshot and return its path."""
    return adb.screenshot()


def wait_for(template: str, timeout: float = config.ACTION_TIMEOUT, threshold: float | None = None) -> tuple[int, int] | None:
    """Poll until *template* appears or *timeout* seconds elapse.
    Pass a custom threshold to override the global config value."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        loc = vision.find_one(grab(), template, threshold=threshold)
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

def _filter_ui_hits(hits: list[tuple[int, int]],
                    screen_w: int = 2560, screen_h: int = 1440) -> list[tuple[int, int]]:
    """Remove hits that land in UI zones (top bar, left/right sidebars)."""
    margin_x = int(screen_w * 0.06)   # ~154px left/right
    margin_top = int(screen_h * 0.10)  # ~144px top bar (coins, level, gems)
    return [
        (x, y) for x, y in hits
        if x > margin_x and x < screen_w - margin_x and y > margin_top
    ]


def _cluster_hits(hits: list[tuple[int, int]], gap: int = 200) -> list[list[tuple[int, int]]]:
    """
    Group detected wheat-top hits into field clusters.
    Hits within *gap* pixels of any member of a cluster belong together.
    Returns a list of clusters, each a list of (x, y) points.
    """
    if not hits:
        return []
    clusters: list[list[tuple[int, int]]] = []
    for pt in sorted(hits, key=lambda p: (p[1], p[0])):
        placed = False
        for cluster in clusters:
            if any(abs(pt[0] - t[0]) < gap and abs(pt[1] - t[1]) < gap for t in cluster):
                cluster.append(pt)
                placed = True
                break
        if not placed:
            clusters.append([pt])
    return clusters


def _cluster_bbox(cluster: list[tuple[int, int]], pad: int = 60) -> tuple[int, int, int, int]:
    """Return (x1, y1, x2, y2) bounding box of a cluster with padding."""
    xs = [p[0] for p in cluster]
    ys = [p[1] for p in cluster]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def state_scan() -> str:
    """
    Look for ready wheat (template: wheat_top.png) or empty plots (template).
    Returns 'harvest', 'plant', or 'wait'.
    """
    print("[SCAN] Taking screenshot...")
    screen = grab()

    wheat_hits = vision.find_all_multi(screen, "wheat_top*.png", threshold=0.55)
    wheat_hits = _filter_ui_hits(wheat_hits)
    if wheat_hits:
        clusters = _cluster_hits(wheat_hits)
        print(f"[SCAN] {len(wheat_hits)} wheat top(s) in {len(clusters)} field(s) — time to harvest.")
        vision.save_debug(screen, wheat_hits)
        return "harvest"

    empty = vision.find_all(screen, "empty_plot.png")
    if empty:
        print(f"[SCAN] {len(empty)} empty plot(s) found — time to plant.")
        vision.save_debug(screen, empty)
        return "plant"

    print("[SCAN] Nothing to do right now.")
    return "wait"



def state_harvest() -> str:
    """
    1. Find all wheat tops via template matching and cluster into fields.
    2. Tap the largest cluster's centre.
    3. Wait for camera to settle, then search the WHOLE screen for scythe.
    4. Re-detect wheat positions (camera may have panned) and sweep from
       scythe across the fresh bounding box.
    5. Repeat until no wheat tops remain.
    """
    attempts = 0
    last_count = None

    while attempts < MAX_ATTEMPTS:
        screen = grab()
        wheat_hits = vision.find_all_multi(screen, "wheat_top*.png", threshold=0.55)
        wheat_hits = _filter_ui_hits(wheat_hits)

        if not wheat_hits:
            print("[HARVEST] All crops harvested.")
            return "scan"

        if len(wheat_hits) == last_count:
            attempts += 1
            print(f"[HARVEST] Hit count unchanged ({len(wheat_hits)}), attempt {attempts}/{MAX_ATTEMPTS}")
        else:
            attempts = 0

        last_count = len(wheat_hits)
        clusters = _cluster_hits(wheat_hits)
        # Pick the largest cluster first (most wheat to harvest)
        clusters.sort(key=len, reverse=True)
        print(f"[HARVEST] {len(wheat_hits)} wheat top(s) in {len(clusters)} field(s)")

        cluster = clusters[0]  # harvest one field per loop pass
        cx = sum(p[0] for p in cluster) // len(cluster)
        cy = sum(p[1] for p in cluster) // len(cluster)

        print(f"[HARVEST] Tapping field centre ({cx}, {cy}), {len(cluster)} hits")
        adb.tap(cx, cy)

        # Wait for camera to settle after tap (Hay Day pans to the field)
        time.sleep(1.5)

        # Search the WHOLE screen for the scythe (camera may have moved)
        deadline = time.time() + 3
        scythe = None
        while time.time() < deadline:
            fresh = grab()
            scythe = vision.find_one(fresh, "harvest_icon.png", threshold=0.40)
            if scythe:
                break
            time.sleep(0.5)

        if not scythe:
            print("[HARVEST] Scythe didn't appear — skipping field.")
            # Tap elsewhere to dismiss any popup
            adb.tap(100, 700)
            time.sleep(0.5)
            continue

        # Re-detect wheat in the FRESH screenshot (positions shifted after camera pan)
        fresh_hits = vision.find_all_multi(fresh, "wheat_top*.png", threshold=0.55)
        fresh_hits = _filter_ui_hits(fresh_hits)

        if fresh_hits:
            x1, y1, x2, y2 = _cluster_bbox(fresh_hits, pad=80)
        else:
            # Fallback: use a generous area around the scythe
            x1, y1 = scythe[0] - 100, scythe[1] - 100
            x2, y2 = scythe[0] + 500, scythe[1] + 500

        # Sweep from scythe to the far corner of the fresh bbox
        sx, sy = scythe
        end_x = x2 + 50 if x2 >= sx else x1 - 50
        end_y = y2 + 50 if y2 >= sy else y1 - 50
        print(f"[HARVEST] Scythe at {scythe}, sweeping → ({end_x}, {end_y})")
        adb.swipe(sx, sy, end_x, end_y, duration_ms=1800)
        time.sleep(1.5)

    print(f"[HARVEST] Could not clear all crops after {MAX_ATTEMPTS} attempts. Moving on.")
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

    print("[BOT] Make sure Hay Day is open and zoomed out to max on your farm.")
    print("[BOT] Starting in 3 seconds...")
    time.sleep(3)

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
