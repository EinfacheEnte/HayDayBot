"""
vision.py
OpenCV-based template matching to locate game elements on screen.
"""

import os
import cv2
import numpy as np
import config


def _load_template(name: str) -> np.ndarray:
    path = os.path.join(config.TEMPLATES_DIR, name)
    template = cv2.imread(path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template not found: {path}")
    return template


def find_one(screenshot_path: str, template_name: str) -> tuple[int, int] | None:
    """
    Find the best single match of *template_name* in the screenshot.
    Returns (x, y) centre of the match, or None if confidence is below threshold.
    """
    screen   = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    template = _load_template(template_name)
    h, w     = template.shape[:2]

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
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
    screen   = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
    template = _load_template(template_name)
    h, w     = template.shape[:2]

    result  = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    matches = []

    # Suppress already-found regions with a black rectangle to avoid duplicates
    result_copy = result.copy()
    while True:
        _, max_val, _, max_loc = cv2.minMaxLoc(result_copy)
        if max_val < config.CONFIDENCE_THRESHOLD:
            break
        cx = max_loc[0] + w // 2
        cy = max_loc[1] + h // 2
        matches.append((cx, cy))
        # Blank out this region so the next iteration finds the next-best match
        x1 = max(0, max_loc[0] - w // 2)
        y1 = max(0, max_loc[1] - h // 2)
        x2 = max_loc[0] + w
        y2 = max_loc[1] + h
        result_copy[y1:y2, x1:x2] = -1

    return sorted(matches, key=lambda p: (p[1], p[0]))  # row-major order


def element_present(screenshot_path: str, template_name: str) -> bool:
    """Returns True if the template is visible on screen."""
    return find_one(screenshot_path, template_name) is not None
