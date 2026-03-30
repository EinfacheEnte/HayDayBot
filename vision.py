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


def find_one(screenshot_path: str, template_name: str) -> tuple[int, int] | None:
    """
    Find the best single match of *template_name* in the screenshot.
    Returns (x, y) centre of the match, or None if below threshold.
    """
    screen = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    if screen is None:
        print(f"[VISION] Could not read screenshot: {screenshot_path}")
        return None

    template, mask = _load_template(template_name)
    h, w = template.shape[:2]

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED, mask=mask)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < config.CONFIDENCE_THRESHOLD:
        return None

    cx = max_loc[0] + w // 2
    cy = max_loc[1] + h // 2
    return cx, cy


def find_all(screenshot_path: str, template_name: str) -> list[tuple[int, int]]:
    """
    Find ALL non-overlapping matches of *template_name* in the screenshot.
    Returns a list of (x, y) centres sorted top-left to bottom-right.
    """
    screen = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    if screen is None:
        print(f"[VISION] Could not read screenshot: {screenshot_path}")
        return []

    template, mask = _load_template(template_name)
    h, w = template.shape[:2]

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED, mask=mask)
    matches = []

    result_copy = result.copy()
    while True:
        _, max_val, _, max_loc = cv2.minMaxLoc(result_copy)
        if max_val < config.CONFIDENCE_THRESHOLD:
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


def element_present(screenshot_path: str, template_name: str) -> bool:
    """Returns True if the template is visible on screen."""
    return find_one(screenshot_path, template_name) is not None
