// Rhea Office — Background Service Worker
const RHEA_CORE = 'http://localhost:8400';

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })
  .catch(err => console.error('Side panel error:', err));

async function getApiKey() {
  const stored = await chrome.storage.local.get(['coreApiKey']);
  return stored.coreApiKey || 'dev-key';
}

// 1. Visual Actuator Relay
chrome.runtime.onMessage.addListener(async (msg, sender) => {
  if (msg.type === "VISUAL_PULSE") {
    const apiKey = await getApiKey();
    try {
      await fetch(`${RHEA_CORE}/actuator/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
        body: JSON.stringify({
          tab_id: sender.tab.id,
          state: msg.data
        })
      });
    } catch (e) {}
  }
});

// 2. Command Polling Loop (The Hands)
async function pollCommands() {
  const apiKey = await getApiKey();
  try {
    const r = await fetch(`${RHEA_CORE}/actuator/command`, {
      headers: { 'X-API-Key': apiKey }
    });
    const cmd = await r.json();
    
    if (cmd.status === "empty" || cmd.detail) return;
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    const result = await chrome.tabs.sendMessage(tab.id, { type: "ACTUATE", command: cmd });
    
    await fetch(`${RHEA_CORE}/actuator/receipt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify({
        command_id: cmd.id,
        status: result.status,
        error: result.error
      })
    });
  } catch (e) {}
}

setInterval(pollCommands, 1000);

// 3. Periodic heartbeat (every 2 min)
chrome.alarms.create('rhea-heartbeat', { periodInMinutes: 2 });
