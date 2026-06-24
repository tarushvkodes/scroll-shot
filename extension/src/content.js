(() => {
  const STATE = {
    lastPointer: null,
    picked: null,
    picking: false
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  function cssPath(element) {
    if (!element || element === document.documentElement) return "html";
    const parts = [];
    let node = element;
    while (node && node.nodeType === Node.ELEMENT_NODE && node !== document.documentElement) {
      let part = node.localName;
      if (node.id) {
        part += `#${CSS.escape(node.id)}`;
        parts.unshift(part);
        break;
      }
      const parent = node.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter((child) => child.localName === node.localName);
        if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(node) + 1})`;
      }
      parts.unshift(part);
      node = parent;
    }
    return parts.join(" > ");
  }

  function resolvePath(path) {
    try {
      return path ? document.querySelector(path) : null;
    } catch {
      return null;
    }
  }

  function isScrollable(element) {
    if (!element || element === document.body) return false;
    const style = getComputedStyle(element);
    const overflowY = style.overflowY;
    const canOverflow = ["auto", "scroll", "overlay"].includes(overflowY);
    return canOverflow && element.scrollHeight - element.clientHeight > 24;
  }

  function scoreScrollable(element, pointer) {
    const rect = element.getBoundingClientRect();
    if (rect.width < 160 || rect.height < 180) return -Infinity;
    const area = rect.width * rect.height;
    const viewportArea = window.innerWidth * window.innerHeight;
    let score = 0;
    score += Math.min(area / viewportArea, 1) * 60;
    score += Math.min((element.scrollHeight - element.clientHeight) / Math.max(1, element.clientHeight), 4) * 30;
    if (pointer && rect.left <= pointer.x && pointer.x <= rect.right && rect.top <= pointer.y && pointer.y <= rect.bottom) {
      score += 120;
      score += (1 - Math.min(area / viewportArea, 1)) * 35;
    }
    const role = `${element.getAttribute("role") || ""} ${element.className || ""}`.toLowerCase();
    if (/chat|message|thread|conversation|direct|scroll|list|feed/.test(role)) score += 35;
    if (rect.width >= window.innerWidth * 0.95 && rect.height >= window.innerHeight * 0.95) score -= 80;
    return score;
  }

  function findTarget() {
    const picked = resolvePath(STATE.picked);
    if (isScrollable(picked)) return picked;

    const pointer = STATE.lastPointer;
    if (pointer) {
      const underPointer = document.elementsFromPoint(pointer.x, pointer.y);
      for (const element of underPointer) {
        let node = element;
        while (node && node !== document.documentElement) {
          if (isScrollable(node)) return node;
          node = node.parentElement;
        }
      }
    }

    const candidates = Array.from(document.querySelectorAll("body *")).filter(isScrollable);
    candidates.sort((a, b) => scoreScrollable(b, pointer) - scoreScrollable(a, pointer));
    return candidates[0] || document.scrollingElement || document.documentElement;
  }

  function showStatus(text) {
    let status = document.getElementById("__scroll_shot_status");
    if (!status) {
      status = document.createElement("div");
      status.id = "__scroll_shot_status";
      Object.assign(status.style, {
        position: "fixed",
        top: "18px",
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: "2147483647",
        padding: "10px 14px",
        borderRadius: "10px",
        background: "rgba(17, 24, 39, 0.92)",
        color: "white",
        font: "600 13px -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        pointerEvents: "none",
        boxShadow: "0 10px 30px rgba(0,0,0,.22)"
      });
      document.documentElement.appendChild(status);
    }
    status.textContent = text;
  }

  function hideStatus() {
    document.getElementById("__scroll_shot_status")?.remove();
  }

  function rectInViewport(element) {
    const rect = element.getBoundingClientRect();
    return {
      left: Math.max(0, Math.floor(rect.left)),
      top: Math.max(0, Math.floor(rect.top)),
      width: Math.min(window.innerWidth, Math.ceil(rect.right)) - Math.max(0, Math.floor(rect.left)),
      height: Math.min(window.innerHeight, Math.ceil(rect.bottom)) - Math.max(0, Math.floor(rect.top))
    };
  }

  async function captureVisible() {
    const response = await chrome.runtime.sendMessage({ type: "captureVisible" });
    if (response?.error) throw new Error(response.error);
    return response.dataUrl;
  }

  async function imageFromDataUrl(dataUrl) {
    const image = new Image();
    image.src = dataUrl;
    await image.decode();
    return image;
  }

  function cropSlice(image, rect, deviceScale) {
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.floor(rect.width * deviceScale));
    canvas.height = Math.max(1, Math.floor(rect.height * deviceScale));
    const ctx = canvas.getContext("2d");
    ctx.drawImage(
      image,
      Math.floor(rect.left * deviceScale),
      Math.floor(rect.top * deviceScale),
      canvas.width,
      canvas.height,
      0,
      0,
      canvas.width,
      canvas.height
    );
    return canvas;
  }

  function hideFixedInside(target) {
    const rect = target.getBoundingClientRect();
    const hidden = [];
    for (const element of document.querySelectorAll("body *")) {
      const style = getComputedStyle(element);
      if (!["fixed", "sticky"].includes(style.position)) continue;
      const item = element.getBoundingClientRect();
      const overlaps = item.right > rect.left && item.left < rect.right && item.bottom > rect.top && item.top < rect.bottom;
      if (!overlaps) continue;
      hidden.push([element, element.style.visibility]);
      element.style.visibility = "hidden";
    }
    return () => {
      for (const [element, visibility] of hidden) element.style.visibility = visibility;
    };
  }

  async function captureTarget() {
    const target = findTarget();
    if (!target) throw new Error("No scroll target found");

    showStatus("Scroll Shot: preparing");
    await sleep(250);

    const originalScroll = target.scrollTop;
    const maxScroll = () => Math.max(0, target.scrollHeight - target.clientHeight);
    const rect = rectInViewport(target);
    const deviceScale = window.devicePixelRatio || 1;
    const step = Math.max(80, Math.floor(target.clientHeight * 0.72));
    const restoreFixed = hideFixedInside(target);
    const frames = [];
    const positions = [];
    let unchanged = 0;

    try {
      target.scrollTop = 0;
      await sleep(500);
      for (let index = 0; index < 300; index += 1) {
        const before = target.scrollTop;
        showStatus(`Scroll Shot: capturing ${index + 1}`);
        const image = await imageFromDataUrl(await captureVisible());
        frames.push(cropSlice(image, rect, deviceScale));
        positions.push(before);

        if (before >= maxScroll() - 2) break;
        target.scrollTop = Math.min(maxScroll(), before + step);
        await sleep(420);
        if (Math.abs(target.scrollTop - before) < 2) {
          unchanged += 1;
          if (unchanged >= 2) break;
        } else {
          unchanged = 0;
        }
      }
    } finally {
      restoreFixed();
      target.scrollTop = originalScroll;
    }

    if (!frames.length) throw new Error("No frames captured");
    showStatus("Scroll Shot: stitching");
    const output = stitchByScrollPosition(frames, positions, deviceScale);
    const dataUrl = output.toDataURL("image/png");
    const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "-");
    await chrome.runtime.sendMessage({
      type: "download",
      dataUrl,
      filename: `scroll-shot-${stamp}.png`
    });
    showStatus("Scroll Shot: saved to Downloads");
    await sleep(1400);
  }

  function stitchByScrollPosition(frames, positions, deviceScale) {
    const width = Math.min(...frames.map((frame) => frame.width));
    const heights = frames.map((frame) => frame.height);
    const yOffsets = positions.map((pos) => Math.round(pos * deviceScale));
    const totalHeight = Math.max(...yOffsets.map((offset, index) => offset + heights[index]));
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = totalHeight;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = "white";
    ctx.fillRect(0, 0, width, totalHeight);
    for (let index = 0; index < frames.length; index += 1) {
      ctx.drawImage(frames[index], 0, 0, width, frames[index].height, 0, yOffsets[index], width, frames[index].height);
    }
    return canvas;
  }

  function startPickMode() {
    STATE.picking = true;
    showStatus("Click the scrollable pane");
  }

  document.addEventListener("mousemove", (event) => {
    STATE.lastPointer = { x: event.clientX, y: event.clientY };
  }, true);

  document.addEventListener("click", (event) => {
    if (!STATE.picking) return;
    event.preventDefault();
    event.stopPropagation();
    let node = event.target;
    while (node && node !== document.documentElement && !isScrollable(node)) node = node.parentElement;
    STATE.picked = cssPath(node || event.target);
    STATE.picking = false;
    showStatus("Scroll Shot: area selected");
    setTimeout(hideStatus, 900);
  }, true);

  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "pick") {
      startPickMode();
      return;
    }
    if (message.type === "capture") {
      captureTarget().catch((error) => {
        showStatus(`Scroll Shot error: ${error.message}`);
        setTimeout(hideStatus, 3000);
      }).finally(() => setTimeout(hideStatus, 1600));
    }
  });
})();
