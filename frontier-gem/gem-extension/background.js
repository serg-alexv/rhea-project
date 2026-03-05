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

/**
 * Inject text into the focused window (Windows only)
 * @param {string} text - The text to inject
 * @param {number} delayMs - Delay between keystrokes in milliseconds
 * @returns {Promise<{success: boolean, message: string}>}
 */
async function injectText(text, delayMs = 50) {
    try {
        const response = await fetch('http://localhost:3456/api/inject', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                delay_ms: delayMs
            })
        });

        const data = await response.json();

        if (response.ok) {
            console.log("✅ Injection successful:", data.message);
            showNotification('✅ Text Injected', `${data.characters} characters typed`);
            return { success: true, message: data.message };
        } else {
            console.error("❌ Injection failed:", data.message);
            showNotification('❌ Injection Failed', data.message);
            return { success: false, message: data.message };
        }
    } catch (error) {
        console.error("❌ Injection error:", error);
        showNotification('❌ Connection Error', 'Cannot reach daemon. Is it running?');
        return { success: false, message: error.message };
    }
}

/**
 * Show desktop notification (using Chrome extensions API)
 */
function showNotification(title, message) {
    chrome.notifications.create({
        type: 'basic',
        iconUrl: '/images/icon-128.png',
        title: title,
        message: message,
        priority: 1
    }, (notificationId) => {
        // Auto-close notification after 5 seconds
        setTimeout(() => {
            chrome.notifications.clear(notificationId);
        }, 5000);
    });
}

/**
 * Context menu handler for injection
 */
chrome.contextMenus?.create?.({
    id: 'inject-ai-response',
    title: 'Inject AI Response (Windows Only)',
    contexts: ['editable']
}, () => {
    if (chrome.runtime.lastError) {
        console.warn("Context menu creation skipped (macOS/Linux):", chrome.runtime.lastError.message);
    }
});

chrome.contextMenus?.onClicked?.addListener?.((info, tab) => {
    if (info.menuItemId === 'inject-ai-response') {
        // This would be triggered with AI-generated text
        // For now, placeholder example
        const exampleText = "This text was injected by Frontier Gem";
        injectText(exampleText, 50);
    }
});

// Listen for messages from other parts of the extension
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'inject') {
        injectText(request.text, request.delayMs || 50)
            .then(sendResponse)
            .catch(error => sendResponse({ success: false, message: error.message }));
        return true; // Indicate async response
    }
});
