# Architecture

Scroll Shot is organized around a platform capture adapter and a shared stitching
pipeline.

## System Components

```text
User Input
  -> Target Selection
  -> Scroll Controller
  -> Frame Capture
  -> Frame Alignment
  -> Stitch Renderer
  -> Exporter
```

## Target Selection

Target selection should support three levels of precision:

- Display: capture a scrolling area on the active monitor.
- Window: capture within a selected app window.
- Region: capture an exact user-drawn rectangle.

Automatic detection is useful, but manual region selection is essential because
many real apps expose incomplete or misleading accessibility trees.

## Scroll Controller

The scroll controller moves the target content and records the expected scroll
direction, step size, and termination condition.

Recommended MVP behavior:

- Start from the current visible position.
- Capture top-to-bottom by default.
- Use a conservative scroll step of 60-75 percent of the selected region height.
- Pause briefly after each scroll for repainting.
- Stop after a repeated frame, an unchanged viewport, or a user-defined maximum.

## Frame Capture

Frame capture should preserve device scale. On macOS, that means handling Retina
coordinates carefully so selection rectangles, captured pixels, and final output
stay aligned.

The capture adapter should return:

- Pixel buffer.
- Display scale.
- Region coordinates.
- Timestamp.
- Window or display metadata when available.

## Frame Alignment

Frame alignment is responsible for finding the overlap between consecutive
captures.

Initial implementation:

- Crop stable horizontal strips from the bottom of frame N and top of frame N+1.
- Compare candidate offsets with normalized cross-correlation or perceptual hash
  matching.
- Ignore known sticky header/footer bands when configured.
- Reject low-confidence matches and ask for manual intervention.

Later implementation:

- Feature matching with OpenCV.
- Text-aware alignment for long documents.
- Dynamic-content masking for cursors, animations, and chat timestamps.

## Stitch Renderer

The stitch renderer composes aligned frames into one image. It should keep a
debug mode that exports intermediate frame positions so stitch bugs are easy to
inspect.

## Exporter

Initial formats:

- PNG.
- JPEG.
- Clipboard.

Later formats:

- PDF.
- TIFF.
- Split images for size-limited destinations.

## Permissions

Scroll Shot should request permissions lazily and explain why they are needed:

- Screen capture for reading pixels.
- Accessibility for scrolling and inspecting UI elements.
- Input monitoring only if a platform feature requires it.

## Current Implementation

The current macOS MVP is implemented as:

- Python CLI in `src/scrollshot`.
- Tk-based region selector in `selection.py`.
- Accessibility-based automatic target detection in `targeting.py` and
  `platform/macos/ScrollShotDetectHelper.swift`.
- Pillow screen capture in `capture.py`.
- OpenCV/Numpy overlap stitching in `stitch.py`.
- Swift/CoreGraphics scroll helper in
  `platform/macos/ScrollShotScrollHelper.swift`.

The helper is compiled into `bin/scrollshot-scroll` by `make build-helper` or
automatically on first run.

## Repository Layout

```text
docs/                 Product and engineering docs
platform/macos/       Native macOS helper code
src/                  Implementation source
.github/              Issue templates and project hygiene
```
