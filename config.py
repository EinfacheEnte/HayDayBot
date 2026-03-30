# ── ADB ──────────────────────────────────────────────────────────────────────
ADB_HOST = "127.0.0.1"
ADB_PORT = 5555          # BlueStacks Air (macOS) default

# ── Vision ───────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.85   # template-match minimum score (0–1)

# ── Timing (seconds) ─────────────────────────────────────────────────────────
TAP_DELAY_BASE   = 0.4   # base pause after every tap
TAP_JITTER       = 0.2   # ± random jitter added to each tap delay
ACTION_TIMEOUT   = 5     # max seconds to wait for a UI element to appear
PLANT_DELAY      = 0.8   # seconds to wait for crop selection menu to appear

# ── Crop ──────────────────────────────────────────────────────────────────────
CROP_GROW_TIME   = 120   # wheat grow time in seconds (2 minutes)

# ── Paths ─────────────────────────────────────────────────────────────────────
SCREENSHOT_PATH  = "/tmp/hayday_frame.png"
TEMPLATES_DIR    = "templates"
