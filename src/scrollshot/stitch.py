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
    score: float


@dataclass(frozen=True)
class StitchResult:
    image: Image.Image
    seams: List[Seam]


def _gray(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)


def find_overlap(previous: Image.Image, current: Image.Image, current_top: int = 0) -> tuple[int, float]:
    prev = _gray(previous)
    curr = _gray(current)
    height, width = prev.shape
    usable_current = curr[current_top:, :]
    usable_height = usable_current.shape[0]
    min_overlap = max(24, int(height * 0.06))
    max_overlap = min(max(min_overlap + 1, int(height * 0.75)), usable_height)

    # Ignore a small side margin; scrollbars and rounded corners can poison seams.
    margin = max(0, int(width * 0.08))
    if width - (margin * 2) > 80:
        prev = prev[:, margin : width - margin]
        usable_current = usable_current[:, margin : width - margin]

    best_overlap = min_overlap
    best_score = float("inf")
    for overlap in range(min_overlap, max_overlap):
        a = prev[-overlap:, :].astype(np.float32)
        b = usable_current[:overlap, :].astype(np.float32)
        score = float(np.mean(np.abs(a - b)))
        if score < best_score:
            best_score = score
            best_overlap = overlap
    return best_overlap, best_score


def detect_sticky_top(previous: Image.Image, current: Image.Image) -> int:
    prev = _gray(previous)
    curr = _gray(current)
    height, width = prev.shape
    max_scan = min(int(height * 0.45), 220)
    if max_scan < 24:
        return 0

    row_diffs = np.mean(np.abs(prev[:max_scan, :].astype(np.float32) - curr[:max_scan, :].astype(np.float32)), axis=1)
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


def stitch_frames(frames: Iterable[Image.Image]) -> StitchResult:
    images = list(frames)
    if not images:
        raise ValueError("no frames to stitch")
    if len(images) == 1:
        return StitchResult(images[0], [])

    width = min(frame.width for frame in images)
    normalized = [frame.crop((0, 0, width, frame.height)).convert("RGB") for frame in images]
    pieces = [normalized[0]]
    seams: List[Seam] = []

    for index, image in enumerate(normalized[1:], start=1):
        sticky_top = detect_sticky_top(normalized[index - 1], image)
        overlap, score = find_overlap(normalized[index - 1], image, current_top=sticky_top)
        crop_top = sticky_top + overlap
        seams.append(Seam(index, overlap, crop_top, sticky_top, score))
        pieces.append(image.crop((0, crop_top, image.width, image.height)))

    total_height = sum(piece.height for piece in pieces)
    output = Image.new("RGB", (width, total_height), "white")
    y = 0
    for piece in pieces:
        output.paste(piece, (0, y))
        y += piece.height

    return StitchResult(output, seams)
