"""
Interactive template cropper — click two corners on the screenshot to crop.

Usage:
  python3 crop_template.py

Controls:
  - Click top-left corner of the wheat top you want
  - Click bottom-right corner
  - Press 's' to save
  - Press 'r' to reset and pick again
  - Press 'q' to quit without saving
"""
import subprocess
import cv2
import sys

ADB_TARGET = "127.0.0.1:5555"

clicks = []
img = None
display = None


def mouse_callback(event, x, y, flags, param):
    global clicks, display
    if event == cv2.EVENT_LBUTTONDOWN:
        # Scale back to original image coordinates
        # Display is scaled to fit screen, so we need to convert
        dh, dw = display.shape[:2]
        oh, ow = img.shape[:2]
        orig_x = int(x * ow / dw)
        orig_y = int(y * oh / dh)

        if len(clicks) < 2:
            clicks.append((orig_x, orig_y))
            print(f"  Click {len(clicks)}: ({orig_x}, {orig_y})")

        if len(clicks) == 2:
            # Draw rectangle on display
            x1 = int(clicks[0][0] * dw / ow)
            y1 = int(clicks[0][1] * dh / oh)
            x2 = int(clicks[1][0] * dw / ow)
            y2 = int(clicks[1][1] * dh / oh)
            display_copy = display.copy()
            cv2.rectangle(display_copy, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.imshow("Crop Template", display_copy)
            print("  Press 's' to save, 'r' to redo, 'q' to quit")


def main():
    global img, display, clicks

    # Take fresh screenshot
    print("[1] Taking ADB screenshot...")
    raw = subprocess.run(
        ["adb", "-s", ADB_TARGET, "exec-out", "screencap", "-p"],
        capture_output=True, timeout=10
    )
    if raw.returncode != 0:
        print("ADB screenshot failed. Is the emulator running?")
        sys.exit(1)

    path = "/tmp/crop_source.png"
    with open(path, "wb") as f:
        f.write(raw.stdout)

    img = cv2.imread(path)
    h, w = img.shape[:2]
    print(f"    Screenshot: {w}x{h}")

    # Scale down to fit on screen (max 1280 wide)
    scale = min(1280 / w, 720 / h)
    display = cv2.resize(img, (int(w * scale), int(h * scale)))

    print()
    print("[2] Click the TOP-LEFT corner of the wheat top, then BOTTOM-RIGHT corner.")
    print("    Zoom: the wheat tips are the golden spiky bits on top of each stalk.")
    print()

    cv2.imshow("Crop Template", display)
    cv2.setMouseCallback("Crop Template", mouse_callback)

    while True:
        key = cv2.waitKey(50) & 0xFF

        if key == ord('q'):
            print("Quit without saving.")
            break

        elif key == ord('r'):
            clicks = []
            display = cv2.resize(img, (int(w * scale), int(h * scale)))
            cv2.imshow("Crop Template", display)
            print("  Reset — click two new corners.")

        elif key == ord('s') and len(clicks) == 2:
            x1 = min(clicks[0][0], clicks[1][0])
            y1 = min(clicks[0][1], clicks[1][1])
            x2 = max(clicks[0][0], clicks[1][0])
            y2 = max(clicks[0][1], clicks[1][1])

            crop = img[y1:y2, x1:x2]
            cw, ch = crop.shape[1], crop.shape[0]
            print(f"\n[3] Cropped: {cw}x{ch} pixels from ({x1},{y1}) to ({x2},{y2})")

            # Auto-number: wheat_top.png, wheat_top2.png, wheat_top3.png, ...
            import glob as globmod
            existing = globmod.glob("templates/wheat_top*.png")
            n = len(existing) + 1
            suffix = "" if n == 1 else str(n)
            out_path = f"templates/wheat_top{suffix}.png"
            cv2.imwrite(out_path, crop)
            print(f"    Saved → {out_path}")

            # Show the cropped template
            preview = cv2.resize(crop, (cw * 4, ch * 4), interpolation=cv2.INTER_NEAREST)
            cv2.imshow("Cropped Template (4x zoom)", preview)
            print("    Press any key to close.")
            cv2.waitKey(0)
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
