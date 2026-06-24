from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from typing import List, Tuple

from PIL import Image, ImageChops, ImageGrab

from .selection import Selection


@dataclass(frozen=True)
class CaptureResult:
    frames: List[Image.Image]
    delta_y: int
    clicked_to_focus: bool
    stopped_reason: str
    unchanged_attempts: int


def capture_region(selection: Selection) -> Image.Image:
    full = ImageGrab.grab().convert("RGB")
    return full.crop(selection.pixel_box)


def frame_changed(previous: Image.Image, current: Image.Image, threshold: float = 1.2) -> bool:
    diff = ImageChops.difference(previous, current).convert("L")
    stat = diff.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
    return stat > threshold


def scroll_once(helper: Path, point: Tuple[int, int], delta_y: int, ticks: int, click: bool = False) -> None:
    command = [str(helper), str(point[0]), str(point[1]), str(delta_y), str(max(1, ticks))]
    if click:
        command.append("click")
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def save_debug_frame(debug_dir: Path | None, image: Image.Image, index: int) -> None:
    if debug_dir is None:
        return
    debug_dir.mkdir(parents=True, exist_ok=True)
    image.save(debug_dir / f"frame-{index:03d}.png")


def calibrate_scroll(
    selection: Selection,
    helper: Path,
    delta_y: int,
    ticks: int,
    delay: float,
    debug_dir: Path | None,
) -> tuple[List[Image.Image], int, bool, str]:
    target = selection.center_point
    first = capture_region(selection)
    save_debug_frame(debug_dir, first, 1)

    attempt = 0
    for click in (False, True):
        for candidate_delta in (delta_y, -delta_y):
            attempt += 1
            scroll_once(helper, target, candidate_delta, ticks, click=click)
            time.sleep(delay)
            image = capture_region(selection)
            if debug_dir is not None:
                image.save(debug_dir / f"calibration-attempt-{attempt}.png")
            if frame_changed(first, image):
                save_debug_frame(debug_dir, image, 2)
                direction = "requested direction" if candidate_delta == delta_y else "opposite direction"
                focus = " after click-to-focus" if click else ""
                return [first, image], candidate_delta, click, f"calibrated with {direction}{focus}"

    return [first], delta_y, False, "selected region did not change after hover-scroll or click-to-focus retries"


def capture_sequence(
    selection: Selection,
    helper: Path,
    frames: int,
    delta_y: int,
    ticks: int,
    delay: float,
    debug_dir: Path | None,
    calibrate: bool = True,
) -> CaptureResult:
    capture_until_stop = frames <= 0
    max_frames = 250 if capture_until_stop else frames

    target = selection.center_point
    unchanged_attempts = 0

    if calibrate and max_frames > 1:
        captured, active_delta, clicked_to_focus, reason = calibrate_scroll(selection, helper, delta_y, ticks, delay, debug_dir)
        if len(captured) == 1:
            return CaptureResult(captured, active_delta, clicked_to_focus, reason, 4)
    else:
        captured = [capture_region(selection)]
        active_delta = delta_y
        clicked_to_focus = False
        reason = "captured requested frame count"
        save_debug_frame(debug_dir, captured[0], 1)

    while len(captured) < max_frames:
        scroll_once(helper, target, active_delta, ticks, click=False)
        time.sleep(delay)
        image = capture_region(selection)
        if not frame_changed(captured[-1], image):
            unchanged_attempts += 1
            reason = "scroll reached the end or the selected region stopped changing"
            break
        captured.append(image)
        save_debug_frame(debug_dir, image, len(captured))

    if capture_until_stop and len(captured) >= max_frames:
        reason = f"stopped at safety limit of {max_frames} frames"

    return CaptureResult(captured, active_delta, clicked_to_focus, reason, unchanged_attempts)
