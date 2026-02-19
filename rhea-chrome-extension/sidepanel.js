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

// Initial Listeners
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "VISUAL_PULSE") {
    log(`Synced: ${msg.data.url}`);
  }
});

// Refresh Loops
setInterval(updateMRI, 2000);

log("Sidekick Online. Eyes Synchronized.");
