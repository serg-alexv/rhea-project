// Rhea Office — Popup Controller
const FIRESTORE_BASE = 'https://firestore.googleapis.com/v1/projects';

let config = { projectId: 'rhea-office-sync', deskName: '', coreApiKey: '' };

async function loadConfig() {
  const stored = await chrome.storage.local.get(['firebaseConfig', 'deskName', 'coreApiKey']);
  if (stored.firebaseConfig) config.projectId = stored.firebaseConfig.projectId;
  if (stored.deskName) config.deskName = stored.deskName;
  if (stored.coreApiKey) config.coreApiKey = stored.coreApiKey;
  
  document.getElementById('projectId').value = config.projectId;
  document.getElementById('deskName').value = config.deskName;
  document.getElementById('coreApiKey').value = config.coreApiKey || '';
}

function fsUrl(collection, docId) {
  const base = `${FIRESTORE_BASE}/${config.projectId}/databases/(default)/documents`;
  return docId ? `${base}/${collection}/${docId}` : `${base}/${collection}`;
}

function extractString(field) {
  if (!field) return '';
  return field.stringValue || field.integerValue || '';
}

async function fetchDesks() {
  try {
    const r = await fetch(fsUrl('agents'));
    const data = await r.json();
    const list = document.getElementById('desksList');
    if (!data.documents || data.documents.length === 0) {
      list.innerHTML = '<li>No desks online</li>';
      document.getElementById('statusDot').className = 'dot dead';
      document.getElementById('statusText').textContent = 'No agents';
      return;
    }
    list.innerHTML = '';
    data.documents.forEach(doc => {
      const f = doc.fields;
      const desk = extractString(f.desk);
      const status = extractString(f.status);
      const lastSeen = extractString(f.last_seen);
      const ago = lastSeen ? timeSince(new Date(lastSeen)) : '?';
      const li = document.createElement('li');
      li.innerHTML = `<strong>${desk}</strong> — ${status} <span style="color:#8b949e">(${ago})</span>`;
      list.appendChild(li);
    });
    document.getElementById('statusDot').className = 'dot alive';
    document.getElementById('statusText').textContent = `${data.documents.length} desk(s) online`;
  } catch (e) {
    document.getElementById('desksList').innerHTML = `<li>Error: ${e.message}</li>`;
    document.getElementById('statusDot').className = 'dot dead';
    document.getElementById('statusText').textContent = 'Offline';
  }
}

async function fetchInbox() {
  try {
    const r = await fetch(fsUrl('inbox'));
    const data = await r.json();
    const list = document.getElementById('inboxList');
    if (!data.documents || data.documents.length === 0) {
      list.innerHTML = '<li>Empty</li>';
      return;
    }
    list.innerHTML = '';
    const unread = data.documents.filter(d =>
      d.fields.read && d.fields.read.booleanValue === false
    );
    const toShow = unread.length > 0 ? unread.slice(-5) : data.documents.slice(-3);
    toShow.forEach(doc => {
      const f = doc.fields;
      const from = extractString(f.from);
      const to = extractString(f.to);
      const msg = extractString(f.message);
      const read = f.read && f.read.booleanValue;
      const li = document.createElement('li');
      li.innerHTML = `<strong>${from}→${to}</strong>: ${msg.substring(0, 60)}${msg.length > 60 ? '...' : ''} ${!read ? '<span class="badge">NEW</span>' : ''}`;
      list.appendChild(li);
    });
  } catch (e) {
    document.getElementById('inboxList').innerHTML = `<li>Error: ${e.message}</li>`;
  }
}

async function sendMessage() {
  const to = document.getElementById('sendTo').value;
  const msg = document.getElementById('sendMsg').value;
  if (!to || !msg || !config.deskName) return;
  try {
    await fetch(fsUrl('inbox'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fields: {
          from: { stringValue: config.deskName },
          to: { stringValue: to },
          message: { stringValue: msg },
          timestamp: { stringValue: new Date().toISOString() },
          read: { booleanValue: false }
        }
      })
    });
    document.getElementById('sendMsg').value = '';
    fetchInbox();
  } catch (e) {
    alert('Send failed: ' + e.message);
  }
}

function timeSince(date) {
  const s = Math.floor((Date.now() - date.getTime()) / 1000);
  if (s < 60) return s + 's ago';
  if (s < 3600) return Math.floor(s / 60) + 'm ago';
  if (s < 86400) return Math.floor(s / 3600) + 'h ago';
  return Math.floor(s / 86400) + 'd ago';
}

document.getElementById('saveConfig').addEventListener('click', async () => {
  const projectId = document.getElementById('projectId').value;
  const deskName = document.getElementById('deskName').value;
  const coreApiKey = document.getElementById('coreApiKey').value;
  
  await chrome.storage.local.set({
    firebaseConfig: { projectId },
    deskName,
    coreApiKey
  });
  
  config = { projectId, deskName, coreApiKey };
  fetchDesks();
  fetchInbox();
  initRealityDeck();
});

document.getElementById('sendBtn').addEventListener('click', sendMessage);
document.getElementById('sendMsg').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') sendMessage();
});

// Reality Deck Logic (Rhea Core API)
const RHEA_CORE = 'http://localhost:8400';

async function fetchMemories() {
  try {
    const r = await fetch(`${RHEA_CORE}/memories`);
    const data = await r.json();
    const select = document.getElementById('memorySelect');
    
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
      headers: { 'Content-Type': 'application/json', 'X-API-Key': config.coreApiKey },
      body: JSON.stringify({ id })
    });
    const res = await r.json();
    if (res.status === 'ok') alert(`Armed: ${id}`);
  } catch (e) {
    alert('Hydration failed. Is Rhea Core running?');
  }
}

async function setStance(mode) {
  try {
    await fetch(`${RHEA_CORE}/modes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': config.coreApiKey },
      body: JSON.stringify({ mode })
    });
    updateStanceUI(mode);
  } catch (e) {
    alert('Stance switch failed.');
  }
}

function updateStanceUI(activeMode) {
  const modes = { 'operator_first': 'stanceOp', 'loop_killer': 'stanceLoop', 'science_rigorous': 'stanceRigor' };
  Object.keys(modes).forEach(m => {
    const btn = document.getElementById(modes[m]);
    if (m === activeMode) {
      btn.style.background = '#238636';
      btn.style.color = 'white';
    } else {
      btn.style.background = '#161b22';
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

document.getElementById('hydrateBtn').addEventListener('click', hydrate);
document.getElementById('stanceOp').addEventListener('click', () => setStance('operator_first'));
document.getElementById('stanceLoop').addEventListener('click', () => setStance('loop_killer'));
document.getElementById('stanceRigor').addEventListener('click', () => setStance('science_rigorous'));

// Init
loadConfig().then(() => {
  fetchDesks();
  fetchInbox();
  initRealityDeck();
});
