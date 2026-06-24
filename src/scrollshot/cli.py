from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import sys

from .capture import capture_sequence
from .selection import choose_region
from .stitch import stitch_frames


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HELPER = ROOT / "bin" / "scrollshot-scroll"


def build_helper(helper: Path) -> None:
    source = ROOT / "platform" / "macos" / "ScrollShotScrollHelper.swift"
    helper.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["swiftc", str(source), "-o", str(helper)], check=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scrollshot",
        description="Capture a high-quality scrolling screenshot from a selected desktop region.",
    )
    parser.add_argument("-o", "--output", type=Path, help="Output PNG path.")
    parser.add_argument("--frames", type=int, default=18, help="Maximum number of frames to capture.")
    parser.add_argument(
        "--delta-y",
        type=int,
        default=-850,
        help="Native scroll delta. Negative usually scrolls down on macOS.",
    )
    parser.add_argument("--delay", type=float, default=0.45, help="Seconds to wait after each scroll.")
    parser.add_argument("--helper", type=Path, default=DEFAULT_HELPER, help="Path to native scroll helper.")
    parser.add_argument("--debug-dir", type=Path, help="Directory for raw frames and seam data.")
    parser.add_argument("--no-build-helper", action="store_true", help="Do not compile the Swift helper.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output = args.output or Path.cwd() / f"scroll-shot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"

    if not args.helper.exists():
        if args.no_build_helper:
            print(f"Missing scroll helper: {args.helper}", file=sys.stderr)
            return 2
        print("Building native macOS scroll helper...")
        build_helper(args.helper)

    print("Select the scrollable region...")
    selection = choose_region()
    if selection is None:
        print("Capture cancelled.")
        return 1

    print("Capturing frames. Keep the target window visible and do not move the pointer.")
    try:
        frames = capture_sequence(
            selection=selection,
            helper=args.helper,
            frames=args.frames,
            delta_y=args.delta_y,
            delay=args.delay,
            debug_dir=args.debug_dir,
        )
    except subprocess.CalledProcessError as exc:
        print("Could not send scroll input. Check macOS Accessibility permission.", file=sys.stderr)
        return exc.returncode or 2

    print(f"Captured {len(frames)} frame(s). Stitching...")
    result = stitch_frames(frames)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.image.save(output, optimize=True)

    if args.debug_dir is not None:
        seam_log = args.debug_dir / "seams.txt"
        seam_log.write_text(
            "\n".join(
                f"frame={seam.frame_index + 1} overlap={seam.overlap} score={seam.score:.3f}"
                for seam in result.seams
            )
            + "\n",
            encoding="utf-8",
        )

    print(f"Saved {output}")
    if result.seams:
        worst = max(result.seams, key=lambda seam: seam.score)
        print(f"Worst seam score: {worst.score:.2f} at frame {worst.frame_index + 1}")
    return 0
