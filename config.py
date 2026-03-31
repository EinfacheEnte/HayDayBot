# ── ADB ──────────────────────────────────────────────────────────────────────
ADB_HOST = "127.0.0.1"
ADB_PORT = 5555          # BlueStacks Air (macOS) default

# ── Vision ───────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.68   # template-match minimum score (0–1)

# ── Timing (seconds) ─────────────────────────────────────────────────────────
TAP_DELAY_BASE   = 0.4   # base pause after every tap
TAP_JITTER       = 0.2   # ± random jitter added to each tap delay
ACTION_TIMEOUT   = 5     # max seconds to wait for a UI element to appear
PLANT_DELAY      = 0.8   # seconds to wait for crop selection menu to appear

# ── Crop ──────────────────────────────────────────────────────────────────────
CROP_GROW_TIME   = 120   # wheat grow time in seconds (2 minutes)
# Minimum pixel area for a wheat colour blob to count as a real field.
# Smaller blobs are decorations/hay bales and get ignored.
WHEAT_MIN_AREA   = 6000
WHEAT_MAX_AREA   = 150000  # ignore blobs larger than this (sky, background, UI)

# ── BlueStacks window ────────────────────────────────────────────────────────
# Height of the BlueStacks toolbar at the top of the window (px).
# The game area starts below this. Adjust if clicks feel offset vertically.
BLUESTACKS_TOOLBAR_HEIGHT = 0

# Internal game resolution (from: adb shell dumpsys window displays)
GAME_W = 2560
GAME_H = 1440

# ── Paths ─────────────────────────────────────────────────────────────────────
SCREENSHOT_PATH  = "/tmp/hayday_frame.png"
TEMPLATES_DIR    = "templates"
