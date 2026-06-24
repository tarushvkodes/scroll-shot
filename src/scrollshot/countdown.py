from __future__ import annotations

import math
from pathlib import Path
import subprocess


def show_hover_countdown(helper: Path, seconds: float) -> None:
    duration = max(1, math.ceil(seconds))
    print(f"Showing {duration}-second visible countdown...")
    subprocess.run([str(helper), str(duration)], check=True)
