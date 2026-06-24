# Scroll Shot Product Spec

## Product Promise

Scroll Shot lets a user take a clean, high-quality scrolling screenshot of any
scrollable content they can see on their desktop, including nested panes and app
interfaces that are not webpages.

## Primary User Stories

- As a user, I can press a shortcut, select a region, and capture a long
  screenshot of that region.
- As a user, I can capture a chat thread even when the chat is inside a fixed
  app window.
- As a user, I can capture a scrolling panel inside a larger page or app without
  including unrelated UI.
- As a user, I can review the stitched result before saving.
- As a user, I can export a lossless PNG for documentation or a compressed JPEG
  for sharing.

## Capture Modes

### Region Capture

The user draws a rectangle around the scrollable part of the screen. Scroll Shot
captures only that rectangle while sending scroll input to the pointer location
or selected accessibility element.

### Window Capture

The user selects a window. Scroll Shot attempts to find scrollable accessibility
elements inside the window and offers the likely target.

### Assisted Capture

If automatic detection fails, the user clicks inside the scrollable area and
Scroll Shot uses that point as the scroll target.

### Manual Step Capture

For difficult surfaces, the user can scroll manually between captures while
Scroll Shot records and stitches frames.

## Quality Requirements

- Preserve native screen scale where possible.
- Prefer PNG for lossless output.
- Use overlap matching to hide seams.
- Detect repeated or unchanged frames to stop capture.
- Warn when animated, loading, or virtualized content may reduce stitch quality.
- Avoid resizing text or UI unless the user explicitly chooses a scale.

## Platform Requirements

### macOS MVP

- Screen Recording permission.
- Accessibility permission for automated scrolling and optional element
  inspection.
- Region picker overlay.
- Mouse-wheel and trackpad-style scroll input.
- Native screenshot capture.

### Windows Follow-Up

- Windows Graphics Capture or Desktop Duplication.
- UI Automation for scrollable element detection.
- Pointer or wheel event injection.

### Linux Follow-Up

- Wayland and X11 need separate capture/input strategies.
- Desktop portal support should be preferred where available.

## Edge Cases

- Virtualized lists that recycle rows.
- Chat apps that load older messages when scrolling upward.
- Sticky headers and footers.
- Scroll momentum.
- Different capture scale between displays.
- Windows that repaint during capture.
- Content with videos, blinking cursors, or animations.
- Apps that block automated input or screen capture.

## Success Criteria

- A non-technical user can capture a nested scrollable area in under 30 seconds.
- The final image has no obvious duplicated bands or missing content.
- The user can capture content outside a browser.
- The app explains permission issues without losing the current capture setup.
