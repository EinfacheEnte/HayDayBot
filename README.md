# HayDayBot

> **Disclaimer** — This project violates Hay Day's [Terms of Service](https://www.supercell.com/en/terms-of-service/). Using it may result in your account being suspended or permanently banned. This repository exists for **educational purposes only** — it demonstrates how computer vision and ADB-based game automation works. **Use at your own risk.**

Automatically plants and harvests wheat on your Hay Day farm running in BlueStacks, using pure ADB input and OpenCV template matching.

## How it works

1. Connects to BlueStacks via ADB (no pyautogui, no window focus needed)
2. Takes a screenshot and uses **multi-template matching** to find wheat tops across all rows of the field
3. Clusters detected wheat tops into field groups and calculates a bounding box for each
4. If crops are ready: taps the field, waits for the scythe to appear, then sweeps it across the full field in one drag
5. If plots are empty: taps each plot and selects wheat from the crop menu
6. Waits for wheat to grow (2 minutes), then repeats

The bot runs entirely through ADB — BlueStacks can be in the background.

---

## Prerequisites

### 1. BlueStacks Air (macOS)

Install **BlueStacks Air** (free, supports Apple Silicon) and log into Hay Day.
Download from: https://www.bluestacks.com/mac

**Important — enable ADB in BlueStacks:**

1. Open BlueStacks
2. Go to **Settings** (gear icon)
3. Navigate to **Advanced**
4. Toggle **Android Debug Bridge (ADB)** to **ON**

Without this, ADB commands will fail with `error: closed`.

- Default ADB address: `127.0.0.1:5555`

### 2. ADB

```bash
brew install android-platform-tools
```

Verify the connection:
```bash
adb connect 127.0.0.1:5555
adb -s 127.0.0.1:5555 shell echo ok
```

### 3. Python dependencies

```bash
pip install -r requirements.txt
```

---

## Template images

The bot needs template images cropped from your emulator to detect wheat, plots, and the harvest scythe. Templates must be cropped **directly from an ADB screenshot** (not from a regular screenshot) so the colors and resolution match exactly.

### Using the crop tool (recommended)

A built-in interactive cropper ensures templates have the correct color profile:

```bash
python3 crop_template.py
```

This takes an ADB screenshot, opens it in a window, and lets you click two corners to crop. Templates are auto-numbered (`wheat_top.png`, `wheat_top2.png`, etc.).

### Required templates

| File | What to capture |
|---|---|
| `templates/wheat_top.png` | Golden spiky tip of a wheat stalk (top portion visible on all rows) |
| `templates/wheat_top2.png` | Same thing from a different row/angle (for better coverage) |
| `templates/wheat_top3.png` | Another angle — more templates = better detection across all rows |
| `templates/harvest_icon.png` | The scythe icon that appears after tapping a ready wheat field |
| `templates/empty_plot.png` | A bare soil plot with no crop planted |
| `templates/wheat_icon.png` | The wheat icon in the crop selection menu |

> **Tip:** Capture 2-3 wheat top templates from different rows (top, middle, bottom) of your field. The bot matches all `wheat_top*.png` files and merges results.

### Manual capture (alternative)

```bash
adb -s 127.0.0.1:5555 exec-out screencap -p > screen.png
```

Open `screen.png`, crop tightly around each element, and save as PNG in the `templates/` folder. **Do not use macOS Preview's File > Export** as it may alter the color profile — use the crop tool instead.

---

## Running the bot

```bash
cd ~/Downloads/HayDayBot-main
python3 bot.py
```

Before starting:
- Open Hay Day in BlueStacks
- Zoom out to maximum (pinch out) so the whole farm is visible
- The bot starts scanning after a 3-second countdown

Stop with `Ctrl+C`.

### Debug output

The bot saves annotated screenshots to `/tmp/`:
- `/tmp/hayday_debug.png` — screenshot with red crosshairs on detected wheat/plots
- `/tmp/hayday_wheat_mask.png` — raw color detection mask (white = detected)

Open these in Preview to verify detection accuracy.

---

## Configuration

Edit `config.py` to change:

| Setting | Default | Description |
|---|---|---|
| `ADB_PORT` | `5555` | BlueStacks ADB port |
| `CONFIDENCE_THRESHOLD` | `0.68` | Template match sensitivity (lower = more lenient) |
| `CROP_GROW_TIME` | `120` | Seconds to wait for wheat to grow |
| `TAP_DELAY_BASE` | `0.4` | Base delay (seconds) after each tap |
| `TAP_JITTER` | `0.2` | Random jitter added to tap delays |
| `WHEAT_MIN_AREA` | `6000` | Minimum pixel area for color-detected wheat blobs |
| `WHEAT_MAX_AREA` | `150000` | Maximum pixel area (filters sky/background) |

## Project structure

```
HayDayBot-main/
  bot.py              # State machine: scan -> harvest/plant -> wait -> scan
  vision.py           # OpenCV template matching + color detection
  adb_controller.py   # Pure ADB input (tap, swipe, screenshot)
  config.py           # All configurable settings
  crop_template.py    # Interactive template cropper tool
  templates/          # Template images (wheat tops, scythe, empty plot, etc.)
  requirements.txt    # Python dependencies (opencv-python, numpy)
```
