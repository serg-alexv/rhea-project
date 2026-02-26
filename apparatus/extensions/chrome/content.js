// Rhea Visual Actuator — Content Script (The Eyes)
// Scrapes interactive elements and executes actuations.

console.log("[Rhea-VAL] Eyes initialized.");

// 1. Element Discovery
function getInteractiveElements() {
  const elements = document.querySelectorAll('button, input, a, [role="button"], [contenteditable="true"]');
  return Array.from(elements).map((el, index) => ({
    id: index,
    tag: el.tagName,
    text: (el.innerText || el.value || el.placeholder || "").substring(0, 50),
    type: el.type || "",
    role: el.getAttribute('role') || "",
    visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
  })).filter(e => e.visible && e.text.trim().length > 0);
}

// 2. State Pulse
function sendVisualPulse() {
  const state = {
    url: window.location.href,
    title: document.title,
    elements: getInteractiveElements()
  };
  chrome.runtime.sendMessage({ type: "VISUAL_PULSE", data: state });
}

// 3. Actuation Execution
function executeActuation(command) {
  console.log("[Rhea-VAL] Executing:", command);
  try {
    const el = document.querySelectorAll('button, input, a, [role="button"]')[command.elementId];
    if (!el) throw new Error("Element not found");

    if (command.action === "CLICK") el.click();
    if (command.action === "TYPE") {
      el.focus();
      el.value = command.text;
      el.dispatchEvent(new Event('input', { bubbles: true }));
    }
    return { status: "SUCCESS" };
  } catch (e) {
    console.error("[Rhea-VAL] Actuation failed:", e);
    return { status: "FAILED", error: e.message };
  }
}

// Listen for commands from background
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "GET_VISUAL_STATE") {
    sendResponse(getInteractiveElements());
  }
  if (msg.type === "ACTUATE") {
    const result = executeActuation(msg.command);
    sendResponse(result);
  }
});

// Initial pulse
setTimeout(sendVisualPulse, 2000);
