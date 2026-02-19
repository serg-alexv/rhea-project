// Rhea Sidekick — Controller
const RHEA_CORE = 'http://localhost:8400';

async function updateMRI() {
  try {
    const r = await fetch(`${RHEA_CORE}/actuator/health`);
    const history = await r.json();
    const container = document.getElementById('mri');
    container.innerHTML = '';
    
    history.forEach(pulse => {
      const bar = document.createElement('div');
      bar.className = 'mri-bar';
      // Height = Logic Depth, Color = Drift (Green to Red)
      const height = pulse.logic_depth * 100;
      const hue = (1 - pulse.drift) * 120; // 120 = Green, 0 = Red
      bar.style.height = `${height}%`;
      bar.style.background = `hsl(${hue}, 70%, 50%)`;
      container.appendChild(bar);
    });
  } catch (e) {}
}

async function updateCouncil() {
  // Placeholder: this will eventually poll a real-time Tribunal event stream
  // For now, we simulate connectivity
}

function log(msg) {
  const feed = document.getElementById('feed');
  const entry = document.createElement('div');
  entry.innerHTML = `<b>[${new Date().toLocaleTimeString()}]</b> ${msg}`;
  feed.prepend(entry);
}

async function fetchMemories() {
  try {
    const r = await fetch(`${RHEA_CORE}/memories`);
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
  const id = document.getElementById('memorySelect').value;
  try {
    const r = await fetch(`${RHEA_CORE}/memories/hydrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': 'dev-key' },
      body: JSON.stringify({ id })
    });
    const res = await r.json();
    if (res.status === 'ok') log(`ARMED: ${id}`);
  } catch (e) {
    log("Arming failed.");
  }
}

async function setStance(mode) {
  try {
    await fetch(`${RHEA_CORE}/modes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': 'dev-key' },
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
  try {
    const r = await fetch(`${RHEA_CORE}/modes`);
    const data = await r.json();
    updateStanceUI(data.active);
  } catch (e) {}
}

// Initial Listeners
document.getElementById('hydrateBtn').addEventListener('click', hydrate);
document.getElementById('stanceOp').addEventListener('click', () => setStance('operator_first'));
document.getElementById('stanceLoop').addEventListener('click', () => setStance('loop_killer'));
document.getElementById('stanceRigor').addEventListener('click', () => setStance('science_rigorous'));

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "VISUAL_PULSE") {
    log(`Synced: ${msg.data.url}`);
  }
});

// Refresh Loops
setInterval(updateMRI, 2000);

log("Sidekick Online. Eyes Synchronized.");
initRealityDeck();
