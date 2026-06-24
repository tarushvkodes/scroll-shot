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
    score: float


@dataclass(frozen=True)
class StitchResult:
    image: Image.Image
    seams: List[Seam]


def _gray(image: Image.Image) -> np.ndarray:
    arr = np.asarray(image.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)


def find_overlap(previous: Image.Image, current: Image.Image) -> tuple[int, float]:
    prev = _gray(previous)
    curr = _gray(current)
    height, width = prev.shape
    min_overlap = max(24, int(height * 0.12))
    max_overlap = max(min_overlap + 1, int(height * 0.92))

    # Ignore a small side margin; scrollbars and rounded corners can poison seams.
    margin = max(0, int(width * 0.08))
    if width - (margin * 2) > 80:
        prev = prev[:, margin : width - margin]
        curr = curr[:, margin : width - margin]

    best_overlap = min_overlap
    best_score = float("inf")
    for overlap in range(min_overlap, max_overlap):
        a = prev[-overlap:, :].astype(np.float32)
        b = curr[:overlap, :].astype(np.float32)
        score = float(np.mean(np.abs(a - b)))
        if score < best_score:
            best_score = score
            best_overlap = overlap
    return best_overlap, best_score


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
        overlap, score = find_overlap(normalized[index - 1], image)
        seams.append(Seam(index, overlap, score))
        pieces.append(image.crop((0, overlap, image.width, image.height)))

    total_height = sum(piece.height for piece in pieces)
    output = Image.new("RGB", (width, total_height), "white")
    y = 0
    for piece in pieces:
        output.paste(piece, (0, y))
        y += piece.height

    return StitchResult(output, seams)
