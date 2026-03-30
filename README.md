# HayDayBot 🌾

> **⚠️ Disclaimer** — This project violates Hay Day's [Terms of Service](https://www.supercell.com/en/terms-of-service/). Using it may result in your account being suspended or permanently banned. This repository exists for **educational purposes only** — it demonstrates how computer vision and ADB-based game automation works. **Use at your own risk.**

Automatically plants and harvests wheat on your Hay Day farm using ADB screenshots and OpenCV template matching.

## How it works

1. Connects to an Android emulator via ADB
2. Takes a screenshot and uses OpenCV template matching to find ready crops or empty plots
3. If crops are ready → clicks the field → clicks the scythe to harvest
4. If plots are empty → clicks each plot → selects wheat from the crop menu
5. Waits for wheat to grow (2 minutes), then repeats

---

## Prerequisites

### 1. Android emulator
Install **BlueStacks Air** (recommended, free, supports Apple Silicon) on your Mac and log into Hay Day.
Download from: https://www.bluestacks.com/mac

- BlueStacks Air ADB port: `127.0.0.1:5555` (default)

### 2. ADB
```bash
brew install android-platform-tools
```

### 3. Python dependencies
```bash
pip install -r requirements.txt
```

---

## Template images (required before running)

Crop these from a live emulator screenshot (`adb exec-out screencap -p > screen.png`, open in Preview):

| File | What to capture |
|---|---|
| `templates/ready_crop.png` | Golden wheat when it's ready to harvest |
| `templates/harvest_icon.png` | The scythe that appears after tapping a ready field |
| `templates/empty_plot.png` | A bare soil plot with no crop planted |
| `templates/wheat_icon.png` | The wheat icon in the crop selection menu |

> Crop tightly (~80–150px). Templates with transparent backgrounds are supported.

---

## Running the bot

```bash
python3 bot.py
```

When prompted, pinch out to maximum zoom in BlueStacks so the whole farm is visible. Stop with `Ctrl+C`.

---

## Configuration

Edit `config.py` to change:

| Setting | Default | Description |
|---|---|---|
| `ADB_PORT` | `5555` | Emulator ADB port |
| `CONFIDENCE_THRESHOLD` | `0.80` | Template match sensitivity (lower = more lenient) |
| `CROP_GROW_TIME` | `120` | Seconds to wait for wheat to grow |
| `TAP_DELAY_BASE` | `0.4` | Base delay (seconds) after each tap |
| `BLUESTACKS_TOOLBAR_HEIGHT` | `0` | Pixels to offset from top of BlueStacks window |
