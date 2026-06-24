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

## Repository Status

This repository is freshly initialized with product direction, architecture, and
project scaffolding. Implementation work should start with the macOS MVP.

## License

MIT
