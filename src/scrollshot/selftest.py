from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .stitch import stitch_frames


def make_test_scroll(width: int = 420, height: int = 1600) -> Image.Image:
    image = Image.new("RGB", (width, height), "#f7f8fb")
    draw = ImageDraw.Draw(image)
    for y in range(height):
        draw.line((0, y, 10, y), fill=(y % 251, (y * 3) % 251, (y * 7) % 251))
    for y in range(0, height, 44):
        fill = (245 - (y // 44) % 30, 248 - (y // 31) % 24, 255 - (y // 19) % 28)
        draw.rectangle((18, y + 8, width - 18, y + 36), fill=fill, outline="#b8c2d6")
        draw.text((32, y + 15), f"Scroll Shot synthetic row {y // 44 + 1:02d} y={y}", fill="#172033")
    return image


def run_selftest(output: Path) -> tuple[Path, int, tuple[int, int]]:
    source = make_test_scroll()
    viewport = 360
    step = 260
    starts = [0, step, step * 2, step * 3]
    frames = [source.crop((0, y, source.width, y + viewport)) for y in starts]
    result = stitch_frames(frames)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.image.save(output, optimize=True)

    expected_height = viewport + (len(frames) - 1) * step
    if result.image.size != (source.width, expected_height):
        raise AssertionError(f"unexpected self-test size: {result.image.size}")
    return output, len(frames), result.image.size


def run_sticky_header_selftest(output: Path) -> tuple[Path, int, tuple[int, int]]:
    source = make_test_scroll(width=420, height=1600)
    header = Image.new("RGB", (420, 72), "#101820")
    draw = ImageDraw.Draw(header)
    draw.text((24, 26), "Pinned header", fill="white")
    viewport = 360
    step = 260
    starts = [0, step, step * 2, step * 3]
    frames = []
    for y in starts:
        body = source.crop((0, y, source.width, y + viewport - header.height))
        frame = Image.new("RGB", (source.width, viewport), "white")
        frame.paste(header, (0, 0))
        frame.paste(body, (0, header.height))
        frames.append(frame)
    result = stitch_frames(frames)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.image.save(output, optimize=True)
    if not any(seam.sticky_top >= 60 for seam in result.seams):
        raise AssertionError("sticky header was not detected")
    if result.image.height < 900:
        raise AssertionError(f"sticky self-test output is suspiciously short: {result.image.size}")
    return output, len(frames), result.image.size
