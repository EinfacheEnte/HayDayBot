# ── ADB ──────────────────────────────────────────────────────────────────────
ADB_HOST = "127.0.0.1"
ADB_PORT = 5555          # BlueStacks Air (macOS) default

# ── Vision ───────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.85   # template-match minimum score (0–1)

# ── Timing (seconds) ─────────────────────────────────────────────────────────
TAP_DELAY_BASE   = 0.4   # base pause after every tap
TAP_JITTER       = 0.2   # ± random jitter added to each tap delay
SCAN_INTERVAL    = 30    # seconds between full farm scans when no weeds found
ACTION_TIMEOUT   = 5     # max seconds to wait for a UI element to appear

# ── Selling ───────────────────────────────────────────────────────────────────
# The bot accepts whatever minimum coin price Hay Day pre-fills for weeds.
# Set SELL_WAIT to give the listing animation time to finish.
SELL_WAIT        = 1.5

# ── Paths ─────────────────────────────────────────────────────────────────────
SCREENSHOT_PATH  = "/tmp/hayday_frame.png"
TEMPLATES_DIR    = "templates"
