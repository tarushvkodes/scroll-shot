from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import sys

from .capture import capture_sequence
from .countdown import show_hover_countdown
from .selection import choose_region
from .selftest import run_selftest, run_sticky_header_selftest
from .stitch import stitch_frames
from .targeting import detect_frontmost_scroll_region


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HELPER = ROOT / "bin" / "scrollshot-scroll"
DEFAULT_DETECT_HELPER = ROOT / "bin" / "scrollshot-detect"
DEFAULT_COUNTDOWN_HELPER = ROOT / "bin" / "scrollshot-countdown"


def build_helper(helper: Path, detect_helper: Path, countdown_helper: Path) -> None:
    helper.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["swiftc", str(ROOT / "platform" / "macos" / "ScrollShotScrollHelper.swift"), "-o", str(helper)], check=True)
    subprocess.run(["swiftc", str(ROOT / "platform" / "macos" / "ScrollShotDetectHelper.swift"), "-o", str(detect_helper)], check=True)
    subprocess.run(["swiftc", str(ROOT / "platform" / "macos" / "ScrollShotCountdownHelper.swift"), "-o", str(countdown_helper)], check=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scrollshot",
        description="Capture a high-quality scrolling screenshot from a selected desktop region.",
    )
    subcommands = parser.add_subparsers(dest="command")

    capture = subcommands.add_parser("capture", help="Capture a scrolling screenshot.")
    capture.add_argument("-o", "--output", type=Path, help="Output PNG path.")
    capture.add_argument("--frames", type=int, default=18, help="Maximum number of frames to capture.")
    capture.add_argument(
        "--delta-y",
        type=int,
        default=750,
        help="Native scroll delta. Scroll Shot will try the opposite direction if this does not move.",
    )
    capture.add_argument(
        "--scroll-ticks",
        type=int,
        default=7,
        help="Wheel events to send for each captured step.",
    )
    capture.add_argument("--delay", type=float, default=0.55, help="Seconds to wait after each scroll.")
    capture.add_argument("--helper", type=Path, default=DEFAULT_HELPER, help="Path to native scroll helper.")
    capture.add_argument("--detect-helper", type=Path, default=DEFAULT_DETECT_HELPER, help="Path to native target detector.")
    capture.add_argument("--countdown-helper", type=Path, default=DEFAULT_COUNTDOWN_HELPER, help="Path to native countdown overlay.")
    capture.add_argument("--debug-dir", type=Path, help="Directory for raw frames and seam data.")
    capture.add_argument("--no-build-helper", action="store_true", help="Do not compile the Swift helper.")
    capture.add_argument(
        "--target",
        choices=("hover", "auto", "manual"),
        default="hover",
        help="How to choose the scrolling region. Default: hover.",
    )
    capture.add_argument("--manual", action="store_true", help="Shortcut for --target manual.")
    capture.add_argument("--hover-delay", type=float, default=5.0, help="Seconds to wait before detecting the region under the pointer.")
    capture.add_argument(
        "--no-calibrate",
        action="store_true",
        help="Skip the first-frame scroll calibration.",
    )

    selftest = subcommands.add_parser("self-test", help="Run a deterministic stitching self-test.")
    selftest.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("scroll-shot-self-test.png"),
        help="Output PNG path for the synthetic stitched image.",
    )
    selftest.add_argument("--sticky-header", action="store_true", help="Include a repeated sticky header in the test.")

    if argv and argv[0].startswith("-") and argv[0] not in ("-h", "--help"):
        argv = ["capture", *argv]
    elif not argv:
        argv = ["capture"]
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.command == "self-test":
        if args.sticky_header:
            output, frame_count, size = run_sticky_header_selftest(args.output)
        else:
            output, frame_count, size = run_selftest(args.output)
        print(f"Self-test stitched {frame_count} frames into {size[0]}x{size[1]} PNG.")
        print(f"Saved {output}")
        return 0

    output = args.output or Path.cwd() / f"scroll-shot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"

    target_mode = "manual" if args.manual else args.target

    needs_countdown = target_mode == "hover"
    if not args.helper.exists() or (target_mode != "manual" and not args.detect_helper.exists()) or (needs_countdown and not args.countdown_helper.exists()):
        if args.no_build_helper:
            print("Missing native helper binary.", file=sys.stderr)
            return 2
        print("Building native macOS helpers...")
        build_helper(args.helper, args.detect_helper, args.countdown_helper)

    if target_mode == "manual":
        print("Select the scrollable region...")
        print("Tip: draw tightly around the content that moves, not the whole window.")
        selection = choose_region()
        if selection is None:
            print("Capture cancelled.")
            return 1
    else:
        if target_mode == "hover":
            print("Move the pointer over the content that should scroll.")
            show_hover_countdown(args.countdown_helper, args.hover_delay)
            use_mouse = True
        else:
            print("Detecting the scrollable region in the frontmost window...")
            use_mouse = False
        try:
            target = detect_frontmost_scroll_region(args.detect_helper, mouse=use_mouse)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else "Automatic detection failed."
            print(stderr, file=sys.stderr)
            print("Falling back to manual selection. Use --target manual to go straight to this mode next time.")
            selection = choose_region()
            if selection is None:
                print("Capture cancelled.")
                return 1
        else:
            selection = target.selection
            print(
                f"Detected {target.role or 'scrollable region'} in {target.app or 'frontmost app'} "
                f"({selection.point_box[2] - selection.point_box[0]}x{selection.point_box[3] - selection.point_box[1]}, score {target.score:.1f})."
            )

    print("Capturing frames.")
    print("Keep the target window visible. Scroll Shot will first test which direction moves the region.")
    try:
        capture = capture_sequence(
            selection=selection,
            helper=args.helper,
            frames=args.frames,
            delta_y=args.delta_y,
            ticks=args.scroll_ticks,
            delay=args.delay,
            debug_dir=args.debug_dir,
            calibrate=not args.no_calibrate,
        )
    except subprocess.CalledProcessError as exc:
        print("Could not send scroll input. Check macOS Accessibility permission.", file=sys.stderr)
        return exc.returncode or 2

    if len(capture.frames) == 1:
        print("Only one frame changed.", file=sys.stderr)
        print("The selected region did not respond to scroll input.", file=sys.stderr)
        print("Try selecting a tighter scrolling pane, or grant Accessibility permission to this terminal app.", file=sys.stderr)
    print(f"Captured {len(capture.frames)} frame(s); {capture.stopped_reason}.")
    print(f"Using scroll delta: {capture.delta_y}")
    if capture.clicked_to_focus:
        print("Used click-to-focus during calibration.")
    print("Stitching...")
    result = stitch_frames(capture.frames)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.image.save(output, optimize=True)

    if args.debug_dir is not None:
        seam_log = args.debug_dir / "seams.txt"
        seam_log.write_text(
            "\n".join(
                (
                    f"frame={seam.frame_index + 1} overlap={seam.overlap} "
                    f"sticky_top={seam.sticky_top} crop_top={seam.crop_top} score={seam.score:.3f}"
                )
                for seam in result.seams
            )
            + "\n",
            encoding="utf-8",
        )

    print(f"Saved {output}")
    if result.seams:
        worst = max(result.seams, key=lambda seam: seam.score)
        print(f"Worst seam score: {worst.score:.2f} at frame {worst.frame_index + 1}")
        sticky_count = sum(1 for seam in result.seams if seam.sticky_top)
        if sticky_count:
            print(f"Removed sticky top bands from {sticky_count} frame(s).")
    return 0
