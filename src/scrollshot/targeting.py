from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Tuple

from PIL import ImageGrab

from .selection import Selection


@dataclass(frozen=True)
class AutoTarget:
    selection: Selection
    app: str
    role: str
    title: str
    score: float


def screen_scale() -> Tuple[float, float]:
    screenshot = ImageGrab.grab()
    # Tk gives reliable logical screen dimensions on macOS without opening UI.
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
    finally:
        root.destroy()
    return screenshot.width / screen_w, screenshot.height / screen_h


def detect_frontmost_scroll_region(helper: Path, *, mouse: bool = False) -> AutoTarget:
    command = [str(helper)]
    if mouse:
        command.append("--mouse")
    completed = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    data = json.loads(completed.stdout)
    x, y = int(data["x"]), int(data["y"])
    w, h = int(data["width"]), int(data["height"])
    scale_x, scale_y = screen_scale()
    point_box = (x, y, x + w, y + h)
    pixel_box = (
        round(point_box[0] * scale_x),
        round(point_box[1] * scale_y),
        round(point_box[2] * scale_x),
        round(point_box[3] * scale_y),
    )
    return AutoTarget(
        selection=Selection(pixel_box, point_box, scale_x, scale_y),
        app=str(data.get("app", "")),
        role=str(data.get("role", "")),
        title=str(data.get("title", "")),
        score=float(data.get("score", 0)),
    )
