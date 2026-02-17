// Rhea Office — Background Service Worker
// Opens side panel on extension icon click

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })
  .catch(err => console.error('Side panel error:', err));

// Periodic heartbeat (every 2 min)
chrome.alarms.create('rhea-heartbeat', { periodInMinutes: 2 });

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'rhea-heartbeat') {
    const config = await chrome.storage.local.get(['firebaseConfig', 'deskName']);
    if (config.firebaseConfig && config.deskName) {
      // Heartbeat via Firestore REST API
      try {
        const projectId = config.firebaseConfig.projectId;
        const desk = config.deskName;
        const url = `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents/agents/${desk}`;
        await fetch(url, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            fields: {
              desk: { stringValue: desk },
              status: { stringValue: 'ALIVE' },
              last_seen: { stringValue: new Date().toISOString() },
              source: { stringValue: 'chrome-extension' }
            }
          })
        });
      } catch (e) {
        console.error('Heartbeat failed:', e);
      }
    }
  }
});
