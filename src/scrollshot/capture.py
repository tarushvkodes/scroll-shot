from __future__ import annotations

from pathlib import Path
import subprocess
import time
from typing import Iterable, List, Tuple

from PIL import Image, ImageChops, ImageGrab

from .selection import Selection


def capture_region(selection: Selection) -> Image.Image:
    full = ImageGrab.grab().convert("RGB")
    return full.crop(selection.pixel_box)


def frame_changed(previous: Image.Image, current: Image.Image, threshold: float = 1.2) -> bool:
    diff = ImageChops.difference(previous, current).convert("L")
    stat = diff.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    return stat > threshold


def scroll_once(helper: Path, point: Tuple[int, int], delta_y: int) -> None:
    subprocess.run(
        [str(helper), str(point[0]), str(point[1]), str(delta_y)],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def capture_sequence(
    selection: Selection,
    helper: Path,
    frames: int,
    delta_y: int,
    delay: float,
    debug_dir: Path | None,
) -> List[Image.Image]:
    if frames < 1:
        raise ValueError("frames must be at least 1")

    captured: List[Image.Image] = []
    target = selection.center_point

    for index in range(frames):
        image = capture_region(selection)
        if captured and not frame_changed(captured[-1], image):
            break
        captured.append(image)
        if debug_dir is not None:
            debug_dir.mkdir(parents=True, exist_ok=True)
            image.save(debug_dir / f"frame-{index + 1:03d}.png")
        if index == frames - 1:
            break
        scroll_once(helper, target, delta_y)
        time.sleep(delay)

    return captured
