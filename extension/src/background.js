chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "captureVisible") {
    chrome.tabs.captureVisibleTab(sender.tab.windowId, { format: "png" }, (dataUrl) => {
      sendResponse({ dataUrl, error: chrome.runtime.lastError?.message });
    });
    return true;
  }

  if (message.type === "download") {
    chrome.downloads.download({
      url: message.dataUrl,
      filename: message.filename,
      saveAs: false
    }, (downloadId) => {
      sendResponse({ downloadId, error: chrome.runtime.lastError?.message });
    });
    return true;
  }
});
