// Rhea Sidekick — Controller (ZEN MODE)
const RHEA_CORE = 'http://localhost:8400';

async function getApiKey() {
  const stored = await chrome.storage.local.get(['coreApiKey']);
  return stored.coreApiKey || 'dev-key';
}

async function updateMRI() {
  const apiKey = await getApiKey();
  try {
    const r = await fetch(`${RHEA_CORE}/actuator/health`, { headers: { 'X-API-Key': apiKey } });
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

async function initRealityDeck() {
  const apiKey = await getApiKey();
  try {
    const r = await fetch(`${RHEA_CORE}/memories`, { headers: { 'X-API-Key': apiKey } });
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
    
    const s = await fetch(`${RHEA_CORE}/modes`, { headers: { 'X-API-Key': apiKey } });
    const sData = await s.json();
    updateStanceUI(sData.active);
  } catch (e) {}
}

function updateStanceUI(activeMode) {
  const modes = { 'operator_first': 'stanceOp', 'loop_killer': 'stanceLoop', 'science_rigorous': 'stanceRigor' };
  Object.keys(modes).forEach(m => {
    const btn = document.getElementById(modes[m]);
    if (!btn) return;
    btn.style.background = (m === activeMode) ? '#238636' : '#21262d';
    btn.style.color = (m === activeMode) ? 'white' : '#8b949e';
  });
}

function log(msg) {
  const feed = document.getElementById('feed');
  if (!feed) return;
  const entry = document.createElement('div');
  entry.style.padding = "4px 0";
  entry.innerHTML = `<span style="color:#58a6ff; font-weight:bold;">[${new Date().toLocaleTimeString()}]</span> ${msg}`;
  feed.prepend(entry);
}

// 2-Hour Hygiene Timer
setInterval(() => {
  const feed = document.getElementById('feed');
  if (feed) feed.innerHTML = `<b>[${new Date().toLocaleTimeString()}]</b> 💠 REFRESHED.`;
}, 7200000);

setInterval(updateMRI, 2000);
initRealityDeck();
log("System Ready. Noise Purged. Objective: High-Level Orchestration.");
