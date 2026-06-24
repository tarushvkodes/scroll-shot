from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class Seam:
    frame_index: int
    overlap: int
    crop_top: int
    sticky_top: int
    crop_bottom: int
    sticky_bottom: int
    score: float


@dataclass(frozen=True)
class StitchResult:
    image: Image.Image
    seams: List[Seam]


def _gray(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)


def find_overlap(
    previous: Image.Image,
    current: Image.Image,
    current_top: int = 0,
    previous_bottom: int = 0,
) -> tuple[int, float]:
    prev = _gray(previous)
    curr = _gray(current)
    height, width = prev.shape
    prev_bottom = max(0, min(previous_bottom, height - 24))
    usable_previous = prev[: height - prev_bottom, :]
    usable_current = curr[current_top:, :]
    usable_height = min(usable_previous.shape[0], usable_current.shape[0])
    min_overlap = max(24, int(height * 0.05))
    max_overlap = min(max(min_overlap + 1, int(height * 0.72)), usable_height)
    if usable_height <= min_overlap:
        return max(1, usable_height), float("inf")

    # Ignore a small side margin; scrollbars and rounded corners can poison seams.
    margin = max(0, int(width * 0.08))
    if width - (margin * 2) > 80:
        usable_previous = usable_previous[:, margin : width - margin]
        usable_current = usable_current[:, margin : width - margin]

    best_overlap = min_overlap
    best_score = float("inf")
    for overlap in range(min_overlap, max_overlap):
        a = usable_previous[-overlap:, :].astype(np.float32)
        b = usable_current[:overlap, :].astype(np.float32)
        score = float(np.mean(np.abs(a - b)))
        if score < best_score:
            best_score = score
            best_overlap = overlap
    return best_overlap, best_score


def detect_sticky_edge(previous: Image.Image, current: Image.Image, edge: str) -> int:
    prev = _gray(previous)
    curr = _gray(current)
    height, _ = prev.shape
    max_scan = min(int(height * 0.45), 220)
    if max_scan < 24:
        return 0

    if edge == "top":
        a = prev[:max_scan, :]
        b = curr[:max_scan, :]
    elif edge == "bottom":
        a = np.flipud(prev[-max_scan:, :])
        b = np.flipud(curr[-max_scan:, :])
    else:
        raise ValueError(f"unknown sticky edge: {edge}")

    row_diffs = np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32)), axis=1)
    sticky = 0
    for diff in row_diffs:
        if diff <= 3.5:
            sticky += 1
        elif sticky > 0:
            # A tiny interruption from cursor blink or antialiasing should not end a header.
            if diff <= 8.0 and sticky < max_scan:
                sticky += 1
                continue
            break
    return sticky if sticky >= 24 else 0


def detect_sticky_top(previous: Image.Image, current: Image.Image) -> int:
    return detect_sticky_edge(previous, current, "top")


def detect_sticky_bottom(previous: Image.Image, current: Image.Image) -> int:
    return detect_sticky_edge(previous, current, "bottom")


def stitch_frames(frames: Iterable[Image.Image]) -> StitchResult:
    images = list(frames)
    if not images:
        raise ValueError("no frames to stitch")
    if len(images) == 1:
        return StitchResult(images[0], [])

    width = min(frame.width for frame in images)
    normalized = [frame.crop((0, 0, width, frame.height)).convert("RGB") for frame in images]
    seams: List[Seam] = []
    top_crops = [0 for _ in normalized]
    bottom_crops = [0 for _ in normalized]

    for index, image in enumerate(normalized[1:], start=1):
        previous = normalized[index - 1]
        sticky_top = detect_sticky_top(previous, image)
        sticky_bottom = detect_sticky_bottom(previous, image)
        overlap, score = find_overlap(
            previous,
            image,
            current_top=sticky_top,
            previous_bottom=sticky_bottom,
        )
        crop_top = sticky_top + overlap
        top_crops[index] = max(top_crops[index], crop_top)
        bottom_crops[index - 1] = max(bottom_crops[index - 1], sticky_bottom)
        seams.append(Seam(index, overlap, crop_top, sticky_top, sticky_bottom, sticky_bottom, score))

    pieces: List[Image.Image] = []
    for index, image in enumerate(normalized):
        top = min(top_crops[index], image.height - 1)
        bottom = max(top + 1, image.height - bottom_crops[index])
        pieces.append(image.crop((0, top, image.width, bottom)))

    total_height = sum(piece.height for piece in pieces)
    output = Image.new("RGB", (width, total_height), "white")
    y = 0
    for piece in pieces:
        output.paste(piece, (0, y))
        y += piece.height

    return StitchResult(output, seams)
