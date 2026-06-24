const captureButton = document.querySelector("#capture");
const pickButton = document.querySelector("#pick");
const state = document.querySelector("#state");

async function send(type) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;
  state.textContent = type === "pick" ? "Pick mode" : "Capturing";
  captureButton.disabled = true;
  pickButton.disabled = true;
  try {
    await chrome.tabs.sendMessage(tab.id, { type });
    if (type === "capture") window.close();
  } catch (error) {
    state.textContent = "Reload page";
    captureButton.disabled = false;
    pickButton.disabled = false;
  }
}

captureButton.addEventListener("click", () => send("capture"));
pickButton.addEventListener("click", () => send("pick"));
