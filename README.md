# HayDayBot 🌾

> **⚠️ Early Access** — This is a work in progress. The current version may not work as expected. A stable release is coming soon.

> **⚠️ Disclaimer** — This project violates Hay Day's [Terms of Service](https://www.supercell.com/en/terms-of-service/). Using it may result in your account being suspended or permanently banned. This repository exists for **educational and illustrative purposes only** — it demonstrates how ADB-based game automation works on Android emulators. **Use at your own risk. The author takes no responsibility for any consequences.**

Automatically harvests weeds on your Hay Day farm and lists them for sale in the roadside shop.

## How it works

1. Connects to an Android emulator via ADB
2. Takes screenshots and uses OpenCV template matching to find weeds
3. Taps each weed → confirms the harvest pop-up
4. Navigates to the roadside shop and lists the weeds at the game's default minimum coin price
5. Sleeps and repeats

---

## Prerequisites

### 1. Android emulator
Install **BlueStacks Air** (recommended, free, supports Apple Silicon) on your Mac and log into Hay Day.
Download from: https://www.bluestacks.com/mac

Alternative: **Android Studio AVD** (more setup, but fully official).

- BlueStacks Air ADB port: `127.0.0.1:5555` (default, no changes needed)
- Android Studio AVD port: varies — check with `adb devices` and update `ADB_PORT` in `config.py`

### 2. ADB
```bash
brew install android-platform-tools
```

### 3. Python dependencies
```bash
pip3 install -r requirements.txt
```

---

## Template images (required before running)

The bot matches game elements against small PNG reference crops stored in `templates/`.
You must capture these yourself from the live emulator:

| File | What to capture |
|---|---|
| `templates/weed.png` | A single weed on the farm grid |
| `templates/harvest_btn.png` | The green "Harvest" pop-up button |
| `templates/shop_icon.png` | The roadside shop building on screen |
| `templates/sell_btn.png` | The empty "For Sale" slot button inside the shop |
| `templates/price_confirm.png` | The "Post" / confirm button after setting a price |

### How to capture a template
1. Take a screenshot of the emulator: `adb exec-out screencap -p > screen.png`
2. Open `screen.png` in Preview (macOS), use the selection tool to crop the element tightly
3. Save the crop as the filename above into the `templates/` folder

> Keep templates small and tight (~50–100 px wide). Avoid including background.

---

## Running the bot

```bash
python3 bot.py
```

Stop with `Ctrl+C`.

---

## Configuration

Edit `config.py` to change:

| Setting | Default | Description |
|---|---|---|
| `ADB_PORT` | `5555` | Emulator ADB port |
| `CONFIDENCE_THRESHOLD` | `0.85` | Template match sensitivity (lower = more lenient) |
| `SCAN_INTERVAL` | `30` | Seconds between scans when no weeds found |
| `TAP_DELAY_BASE` | `0.4` | Base delay (seconds) after each tap |
