"""
vision.py
OpenCV-based template matching to locate game elements on screen.
Supports templates with transparent backgrounds (RGBA) via alpha masking.
"""

import os
import cv2
import numpy as np
import config


def _load_template(name: str) -> tuple[np.ndarray, np.ndarray | None]:
    """
    Load a template image and return (bgr_image, mask).
    If the template has an alpha channel, the mask is derived from it
    so transparent pixels are ignored during matching.
    """
    path = os.path.join(config.TEMPLATES_DIR, name)
    template = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if template is None:
        raise FileNotFoundError(f"Template not found: {path}")

    if template.shape[2] == 4:
        # Split into BGR + alpha
        bgr  = template[:, :, :3]
        alpha = template[:, :, 3]
        # Mask: 255 where opaque, 0 where transparent
        mask = alpha
        return bgr, mask
    else:
        return template, None


def find_one(screenshot_path: str, template_name: str, threshold: float | None = None) -> tuple[int, int] | None:
    """
    Find the best single match of *template_name* in the screenshot.
    Returns (x, y) centre of the match, or None if below threshold.
    Pass a custom threshold to override the global config value.
    """
    cutoff = threshold if threshold is not None else config.CONFIDENCE_THRESHOLD

    screen = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    if screen is None:
        print(f"[VISION] Could not read screenshot: {screenshot_path}")
        return None

    template, mask = _load_template(template_name)
    h, w = template.shape[:2]

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED, mask=mask)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    print(f"[VISION] {template_name}: best score {max_val:.3f} (threshold {cutoff})")

    if max_val < cutoff:
        return None

    cx = max_loc[0] + w // 2
    cy = max_loc[1] + h // 2
    return cx, cy


def find_all(screenshot_path: str, template_name: str,
             threshold: float | None = None) -> list[tuple[int, int]]:
    """
    Find ALL non-overlapping matches of *template_name* in the screenshot.
    Returns a list of (x, y) centres sorted top-left to bottom-right.
    *threshold* overrides config.CONFIDENCE_THRESHOLD if given.
    """
    thresh = threshold if threshold is not None else config.CONFIDENCE_THRESHOLD

    screen = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    if screen is None:
        print(f"[VISION] Could not read screenshot: {screenshot_path}")
        return []

    template, mask = _load_template(template_name)
    h, w = template.shape[:2]

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED, mask=mask)
    matches = []

    result_copy = result.copy()
    first = True
    while True:
        _, max_val, _, max_loc = cv2.minMaxLoc(result_copy)
        if first:
            print(f"[VISION] {template_name}: best score {max_val:.3f} (threshold {thresh})")
            first = False
        if max_val < thresh:
            break
        cx = max_loc[0] + w // 2
        cy = max_loc[1] + h // 2
        matches.append((cx, cy))
        # Blank out this region to find the next match
        x1 = max(0, max_loc[0] - w // 2)
        y1 = max(0, max_loc[1] - h // 2)
        x2 = max_loc[0] + w
        y2 = max_loc[1] + h
        result_copy[y1:y2, x1:x2] = -1

    return sorted(matches, key=lambda p: (p[1], p[0]))  # row-major order


def find_all_multi(screenshot_path: str, pattern: str,
                   threshold: float | None = None) -> list[tuple[int, int]]:
    """
    Run find_all with every template matching *pattern* (glob) in the
    templates directory, merge results, and de-duplicate nearby points.

    Example: find_all_multi(screen, "wheat_top*.png", threshold=0.55)
    will match wheat_top.png, wheat_top2.png, wheat_top3.png, etc.
    """
    import glob as globmod

    template_files = sorted(globmod.glob(os.path.join(config.TEMPLATES_DIR, pattern)))
    if not template_files:
        print(f"[VISION] No templates matching '{pattern}' in {config.TEMPLATES_DIR}")
        return []

    all_hits: list[tuple[int, int]] = []
    for tpath in template_files:
        tname = os.path.basename(tpath)
        hits = find_all(screenshot_path, tname, threshold=threshold)
        all_hits.extend(hits)

    # De-duplicate: if two hits from different templates are within 40px,
    # keep only one (they're detecting the same wheat stalk)
    if not all_hits:
        return []

    deduped: list[tuple[int, int]] = []
    for pt in sorted(all_hits, key=lambda p: (p[1], p[0])):
        if not any(abs(pt[0] - d[0]) < 40 and abs(pt[1] - d[1]) < 40 for d in deduped):
            deduped.append(pt)

    return deduped


def find_near(screenshot_path: str, template_name: str, cx: int, cy: int,
              left: int = 700, right: int = 100, above: int = 500, below: int = 100,
              threshold: float | None = None) -> tuple[int, int] | None:
    """
    Like find_one but only searches in an asymmetric region around (cx, cy).
    In Hay Day the scythe always appears to the upper-left of the field so we
    search mostly left/above and only a little right/below by default.
    Coordinates are in the full screenshot space and so is the returned point.
    """
    cutoff = threshold if threshold is not None else config.CONFIDENCE_THRESHOLD

    screen = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    if screen is None:
        print(f"[VISION] Could not read screenshot: {screenshot_path}")
        return None

    sh, sw = screen.shape[:2]
    x1 = max(0, cx - left)
    y1 = max(0, cy - above)
    x2 = min(sw, cx + right)
    y2 = min(sh, cy + below)
    roi = screen[y1:y2, x1:x2]

    template, mask = _load_template(template_name)
    th, tw = template.shape[:2]

    if roi.shape[0] < th or roi.shape[1] < tw:
        return None

    result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED, mask=mask)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    print(f"[VISION] {template_name} (near {cx},{cy}): best score {max_val:.3f} (threshold {cutoff})")

    if max_val < cutoff:
        return None

    # Convert ROI-local coords back to full screenshot coords
    fx = x1 + max_loc[0] + tw // 2
    fy = y1 + max_loc[1] + th // 2
    return fx, fy


def element_present(screenshot_path: str, template_name: str) -> bool:
    """Returns True if the template is visible on screen."""
    return find_one(screenshot_path, template_name) is not None


def find_wheat_regions(screenshot_path: str) -> list[dict]:
    """
    Detect ready wheat fields using color rather than template matching.
    Wheat is a bright, saturated golden-yellow — we find all contiguous blobs
    of that colour and filter by minimum area to discard small decorations
    (hay bales, UI icons, path edges) that share similar hues.

    Returns a list of dicts with:
        center  – (cx, cy) centroid of the blob, good for tapping
        bbox    – (x1, y1, x2, y2) bounding box, used to plan the sweep
        area    – pixel area of the blob
    sorted top-left → bottom-right.
    """
    screen = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    if screen is None:
        print(f"[VISION] Could not read screenshot: {screenshot_path}")
        return []

    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)

    # Wheat golden-yellow in HSV.
    # Hue 20-35 = golden yellow (wheat); raised sat floor to 160 to cut out
    # dull tan mud/dirt which shares the hue but has much lower saturation.
    lower = np.array([20, 160, 160])
    upper = np.array([35, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    # Morphological cleanup — order matters!
    # 1. Close FIRST (9x9) — fills internal gaps/holes in the wheat blob,
    #    making it one solid diamond shape that can survive aggressive erosion.
    # 2. Open SECOND (13x13) — erodes then dilates. The now-solid wheat block
    #    (~300+ px wide) shrinks by 12px per side and survives. Scattered pig
    #    pen mud spots (~20-40px each) are completely wiped out by the erosion.
    k_close = np.ones((9, 9), np.uint8)
    k_open  = np.ones((13, 13), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k_open)

    # Save the raw colour mask so you can inspect it in Preview
    cv2.imwrite("/tmp/hayday_wheat_mask.png", mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    sh, sw = screen.shape[:2]
    # Left and right UI strips (sidebar icons, coins, etc.) — ignore blobs here
    UI_MARGIN_X = int(sw * 0.06)   # ~154px on 2560-wide screen

    regions = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < config.WHEAT_MIN_AREA or area > config.WHEAT_MAX_AREA:
            continue

        # Solidity: wheat fields are solid shapes (0.6+).
        # Scattered mud patches have a large convex hull but sparse fill → low solidity.
        hull_area = cv2.contourArea(cv2.convexHull(c))
        if hull_area == 0:
            continue
        solidity = area / hull_area
        if solidity < 0.60:
            continue

        x, y, w, h = cv2.boundingRect(c)

        # Skip blobs that sit entirely inside the left/right UI strips
        if x + w < UI_MARGIN_X or x > sw - UI_MARGIN_X:
            continue

        M = cv2.moments(c)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        regions.append({"center": (cx, cy), "bbox": (x, y, x + w, y + h), "area": area})
        print(f"[VISION] wheat region: center=({cx},{cy}) area={int(area)} solidity={solidity:.2f} bbox=({x},{y},{x+w},{y+h})")

    return sorted(regions, key=lambda r: (r["center"][1], r["center"][0]))


def save_debug(screenshot_path: str, points: list[tuple[int, int]], out_path: str = "/tmp/hayday_debug.png") -> None:
    """
    Save a copy of the screenshot with circles drawn at each detected point.
    Open /tmp/hayday_debug.png in Preview to see exactly what the bot sees.
    """
    screen = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    if screen is None:
        return
    for (x, y) in points:
        cv2.circle(screen, (x, y), 40, (0, 0, 255), 4)     # red circle
        cv2.line(screen, (x - 50, y), (x + 50, y), (0, 0, 255), 3)  # crosshair
        cv2.line(screen, (x, y - 50), (x, y + 50), (0, 0, 255), 3)
    cv2.imwrite(out_path, screen)
    print(f"[DEBUG] Saved annotated screenshot → {out_path}")
