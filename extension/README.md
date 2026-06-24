# Scroll Shot Browser Extension

Chrome/Atlas extension for DOM-aware scrolling screenshots.

## Install In Atlas Or Chrome

1. Open the extensions page.
   - Chrome: `chrome://extensions`
   - Atlas: use its Chromium extensions/settings UI.
2. Enable Developer Mode.
3. Click Load unpacked.
4. Select this folder:

```text
extension
```

## Use

1. Open the page or chat you want to capture.
2. Hover your pointer over the scrollable chat/message pane.
3. Click the Scroll Shot extension icon.
4. Click Capture scroll area.
5. The PNG downloads automatically.

If it picks the wrong area:

1. Click Pick area on page.
2. Click the actual scrollable pane.
3. Open the extension again and click Capture scroll area.

## Why This Is Better For Browser Chats

The extension uses DOM scroll position and element geometry instead of desktop
pixels. That means it can isolate nested scroll panes and avoid repeatedly
capturing browser sidebars, sticky headers, and chat input bars.
