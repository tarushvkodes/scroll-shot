# Scroll Shot

High-quality scrolling screenshots anywhere.

Scroll Shot is a desktop-first tool for capturing long screenshots from any
scrollable surface: websites, chat apps, document panes, settings panels,
embedded lists, terminal views, and partial regions inside a window. It is meant
to work even when the whole page does not scroll and only one area of the window
has scrollable content.

## Why This Exists

Most scrolling screenshot tools assume the target is a browser page. That misses
the places where people actually need evidence, records, or polished captures:
chat threads, app sidebars, modals, support dashboards, desktop apps, nested
panes, and UI regions that cannot be exported cleanly.

Scroll Shot treats scrolling screenshot capture as a desktop interaction problem,
not just a web automation problem.

## Goals

- Capture full-length screenshots from any visible scrollable region.
- Let users select a window, a full screen, or a specific region inside a window.
- Support nested and partial scrolling areas.
- Produce crisp, high-resolution output with minimal seams and compression loss.
- Handle dynamic interfaces such as chats, feeds, and virtualized lists.
- Keep the workflow simple enough for a quick keyboard shortcut.

## Non-Goals

- Bypassing app permissions, DRM, paywalls, or security controls.
- Capturing content the user cannot already view on their own desktop.
- Building only a browser extension.

## Capture Model

Scroll Shot uses a capture pipeline built around visible desktop state:

1. Select the target window or region.
2. Detect or confirm the scrollable area.
3. Capture the current viewport at native scale.
4. Scroll by a calibrated step.
5. Capture the next viewport.
6. Align overlapping frames.
7. Stitch frames into a final image.
8. Export PNG, JPEG, PDF, or clipboard output.

The long-term target is "works anywhere the user can scroll," with platform
specific implementations for macOS, Windows, and Linux.

## MVP Scope

The first MVP should focus on macOS because the platform has strong primitives
for screen capture, accessibility inspection, and input automation:

- Region selection overlay.
- Manual scroll-region selection.
- Mouse-wheel based capture loop.
- Native-resolution frame capture.
- Overlap-based image stitching.
- PNG export.
- Basic retry controls for dynamic content.

See [docs/product-spec.md](docs/product-spec.md) and
[docs/architecture.md](docs/architecture.md) for the initial product and
technical plan.

## Current MVP

Scroll Shot now includes:

- Browser/Atlas extension for DOM-aware scrolling screenshots.
- Drag-to-select region picker.
- Hover-to-target automatic scroll region detection.
- Frontmost-window automatic scroll region detection.
- Native desktop screenshot capture.
- Native macOS scroll input helper.
- Multi-frame capture loop with first-run scroll direction calibration.
- Capture-until-stop by default, with a high safety cap.
- Overlap-based image stitching.
- Sticky header and sticky bottom bar removal for chat-style interfaces.
- Lossless PNG export.
- Optional debug frame export.
- Deterministic stitching self-test.

This is an early prototype. It is already useful for scrollable desktop regions,
but difficult targets such as virtualized lists, sticky headers, and animated
chat UIs may still need tuning.

## Quick Start

### Browser Extension

For browser chats and pages, use the extension first. It is more accurate than
desktop capture because it can use DOM scroll positions.

Load this folder as an unpacked Chrome/Atlas extension:

```text
extension
```

Then hover the chat pane, click the extension icon, and choose Capture scroll
area. See [extension/README.md](extension/README.md).

### Desktop Tool

```bash
make capture
```

Then move your pointer over the content that should scroll during the visible
five-second countdown. Scroll Shot asks macOS Accessibility for the UI region
under the pointer and captures that region. No drawing is needed.

Keep the target visible while Scroll Shot captures and scrolls.
By default, capture continues until the selected region stops moving.

The default output is written to `~/Downloads` as:

```text
scroll-shot-YYYYMMDD-HHMMSS.png
```

## CLI

```bash
PYTHONPATH=src python3 -m scrollshot --help
```

Useful options:

```bash
PYTHONPATH=src python3 -m scrollshot capture \
  --output captures/thread.png \
  --frames 0 \
  --hover-delay 5 \
  --delta-y 520 \
  --scroll-ticks 4 \
  --delay 0.55 \
  --debug-dir debug-frames/thread
```

`--frames 0` is the default and means "keep going until scrolling stops." Use a
positive value only when you want to cap a capture early.

Targeting modes:

```bash
# Default: hover over the scrollable content during the countdown.
PYTHONPATH=src python3 -m scrollshot capture --target hover

# Fully automatic: choose the best-looking scrollable region in the frontmost window.
PYTHONPATH=src python3 -m scrollshot capture --target auto

# Fallback: draw a region manually.
PYTHONPATH=src python3 -m scrollshot capture --target manual
```

Automatic hover targeting does not fall back to the manual overlay. If macOS has
not granted Accessibility permission yet, Scroll Shot exits and tells you what
permission to enable.

Run the deterministic stitcher test:

```bash
make self-test
```

That creates `scroll-shot-self-test.png` from synthetic scrolling frames and
checks the final stitched dimensions.

### macOS Permissions

Scroll Shot may need:

- Screen Recording permission to read pixels.
- Accessibility permission to detect UI regions and send scroll input.

If scrolling does not happen, open System Settings and grant Accessibility
permission to the terminal app running Scroll Shot.

If Scroll Shot captures only one frame, it means the selected area did not
visibly change after it tried both scroll directions. Usually that means the
detected target was not the scrolling pane, the content was already at the end,
or Accessibility permission is missing.

## Development

Compile the native scroll helper:

```bash
make build-helper
```

Run from source:

```bash
PYTHONPATH=src python3 -m scrollshot
```

## License

MIT
