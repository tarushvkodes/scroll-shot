# Contributing

Thanks for helping build Scroll Shot.

## Development Principles

- Build for real desktop interfaces, not only ideal browser pages.
- Preserve image quality by default.
- Prefer explicit user control when automatic detection is uncertain.
- Keep platform-specific capture code behind clear adapters.
- Add debug output for every stitching algorithm change.

## First Areas To Work On

- macOS screen capture adapter.
- Region picker overlay.
- Scroll-step calibration.
- Image overlap detection.
- Debug exports for failed stitches.

## Reporting Bugs

When reporting a capture failure, include:

- Operating system and version.
- App being captured.
- Capture mode.
- Whether the target is a full page, window, or nested region.
- A description of the visual failure, such as duplicate rows, missing bands, or
  distorted seams.

Do not upload private screenshots unless you have reviewed and redacted them.
