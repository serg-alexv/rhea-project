let port = null;
const HEARTBEAT_INTERVAL = 5 * 60 * 1000;  // 5 minutes in milliseconds
const IDLE_TIMEOUT = 30 * 60 * 1000;       // 30 minutes idle timeout
let lastActivityTime = Date.now();
let heartbeatTimerId = null;
let idleTimerId = null;

function connect() {
    console.log("🔌 Attempting native connection to com.rhea.frontier_gem...");
    port = chrome.runtime.connectNative('com.rhea.frontier_gem');

    port.onMessage.addListener((msg) => {
        console.log("📥 From Gem Bus:", msg);
        lastActivityTime = Date.now();
        resetIdleTimer();
    });

    port.onDisconnect.addListener(() => {
        const error = chrome.runtime.lastError ? chrome.runtime.lastError.message : "Unknown";
        console.warn(`🔌 Bus Disconnected (${error}). Retrying in 5s...`);
        port = null;
        clearTimeout(heartbeatTimerId);
        clearTimeout(idleTimerId);
        setTimeout(connect, 5000);
    });

    // Start heartbeat timer
    startHeartbeat();
}

function startHeartbeat() {
    if (heartbeatTimerId) clearTimeout(heartbeatTimerId);
    
    heartbeatTimerId = setInterval(() => {
        if (port) {
            const heartbeat = {
                type: "heartbeat",
                timestamp: Date.now(),
                uptime: Math.floor((Date.now() - lastActivityTime) / 1000)
            };
            
            try {
                port.postMessage(heartbeat);
                console.log("💓 Heartbeat sent @ " + new Date(heartbeat.timestamp).toLocaleTimeString());
            } catch (e) {
                console.error("❌ Heartbeat failed:", e);
                clearInterval(heartbeatTimerId);
            }
        }
    }, HEARTBEAT_INTERVAL);
}

function resetIdleTimer() {
    if (idleTimerId) clearTimeout(idleTimerId);
    
    idleTimerId = setTimeout(() => {
        console.warn("😴 Service Worker idle for 30 minutes. Sending idle signal...");
        if (port) {
            const idleSignal = {
                type: "idle",
                timestamp: Date.now(),
                reason: "idle_timeout"
            };
            
            try {
                port.postMessage(idleSignal);
            } catch (e) {
                console.error("❌ Idle signal failed:", e);
            }
        }
    }, IDLE_TIMEOUT);
}

// Tab activation listener - update activity time
chrome.tabs.onActivated.addListener(activeInfo => {
    lastActivityTime = Date.now();
    resetIdleTimer();
    
    if (!port) return;

    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (chrome.runtime.lastError) return;

        const observation = {
            event: "tab_focus",
            url: tab.url,
            title: tab.title,
            timestamp: Date.now()
        };

        try {
            port.postMessage(observation);
            console.log("📤 Tab Focus Sent:", observation.title);
        } catch (e) {
            console.error("❌ Pipe broken:", e);
        }
    });
});

// Tab update listener - update activity time
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    lastActivityTime = Date.now();
    resetIdleTimer();
});

// Web request listener - update activity time (if available)
chrome.webRequest?.onBeforeRequest?.addListener?.(
    (details) => {
        lastActivityTime = Date.now();
        resetIdleTimer();
    },
    { urls: ["<all_urls>"] }
);

// Initial connection
connect();
