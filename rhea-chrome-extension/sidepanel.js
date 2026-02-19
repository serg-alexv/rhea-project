// Rhea Sidekick — Controller
const RHEA_CORE = 'http://localhost:8400';

async function getApiKey() {
  const stored = await chrome.storage.local.get(['coreApiKey']);
  return stored.coreApiKey || 'dev-key';
}

async function updateMRI() {
  const apiKey = await getApiKey();
  try {
    const r = await fetch(`${RHEA_CORE}/actuator/health`, {
      headers: { 'X-API-Key': apiKey }
    });
    const history = await r.json();
    const container = document.getElementById('mri');
    if (!container) return;
    container.innerHTML = '';
    
    history.forEach(pulse => {
      const bar = document.createElement('div');
      bar.className = 'mri-bar';
      const height = pulse.logic_depth * 100;
      const hue = (1 - pulse.drift) * 120; 
      bar.style.height = `${height}%`;
      bar.style.background = `hsl(${hue}, 70%, 50%)`;
      container.appendChild(bar);
    });
  } catch (e) {}
}

async function fetchMemories() {
  const apiKey = await getApiKey();
  try {
    const r = await fetch(`${RHEA_CORE}/memories`, {
      headers: { 'X-API-Key': apiKey }
    });
    const data = await r.json();
    const select = document.getElementById('memorySelect');
    if (!select) return;
    
    while (select.options.length > 1) select.remove(1);
    data.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = `${m.type === 'SNAPSHOT' ? '🕒' : '💠'} ${m.id}`;
      select.appendChild(opt);
    });
  } catch (e) {}
}

async function hydrate() {
  const apiKey = await getApiKey();
  const id = document.getElementById('memorySelect').value;
  try {
    const r = await fetch(`${RHEA_CORE}/memories/hydrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify({ id })
    });
    const res = await r.json();
    if (res.status === 'ok') log(`ARMED: ${id}`);
  } catch (e) {
    log("Arming failed.");
  }
}

async function setStance(mode) {
  const apiKey = await getApiKey();
  try {
    await fetch(`${RHEA_CORE}/modes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify({ mode })
    });
    updateStanceUI(mode);
    log(`Stance: ${mode}`);
  } catch (e) {}
}

function updateStanceUI(activeMode) {
  const modes = { 'operator_first': 'stanceOp', 'loop_killer': 'stanceLoop', 'science_rigorous': 'stanceRigor' };
  Object.keys(modes).forEach(m => {
    const btn = document.getElementById(modes[m]);
    if (!btn) return;
    if (m === activeMode) {
      btn.style.background = '#238636';
      btn.style.color = 'white';
    } else {
      btn.style.background = '#21262d';
      btn.style.color = '#8b949e';
    }
  });
}

async function initRealityDeck() {
  await fetchMemories();
  const apiKey = await getApiKey();
  try {
    const r = await fetch(`${RHEA_CORE}/modes`, {
      headers: { 'X-API-Key': apiKey }
    });
    const data = await r.json();
    updateStanceUI(data.active);
  } catch (e) {}
}

function log(msg) {
  const feed = document.getElementById('feed');
  if (!feed) return;
  const entry = document.createElement('div');
  entry.innerHTML = `<b>[${new Date().toLocaleTimeString()}]</b> ${msg}`;
  feed.prepend(entry);
}

// 2-Hour Hygiene Timer (The Clean Slate Protocol)
function cleanSlate() {
  const feed = document.getElementById('feed');
  if (feed) {
    feed.innerHTML = `<b>[${new Date().toLocaleTimeString()}]</b> 💠 CONTEXT PURGE COMPLETE. Slate is clean.`;
    log("Reminder: Node-01, run 'clear' in your terminal to maintain zero-drift focus.");
  }
}

// Set interval for 2 hours (2 * 60 * 60 * 1000)
setInterval(cleanSlate, 7200000);

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "VISUAL_PULSE") {
    log(`Synced: ${msg.data.url}`);
  }
});

setInterval(updateMRI, 2000);
log("Sidekick Online. Eyes Synchronized.");
initRealityDeck();
