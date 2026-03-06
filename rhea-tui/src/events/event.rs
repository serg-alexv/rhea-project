use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Core event struct—represents any event flowing through the system.
/// Never breaks the stream: malformed input becomes a raw event.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Event {
    pub version: String,
    pub actor: String,           // "daemon", "cli", "chrome", "ai", etc.
    pub event_type: String,      // "state", "log", "task", "discovery", etc.
    pub payload: Value,          // JSON value (can be any structure)
    pub timestamp: i64,          // Unix timestamp in milliseconds
}

impl Event {
    /// Create event from valid JSON
    pub fn from_json(json: Value) -> Self {
        Self {
            version: json.get("version").and_then(|v| v.as_str()).unwrap_or("1.0").to_string(),
            actor: json.get("actor").and_then(|v| v.as_str()).unwrap_or("unknown").to_string(),
            event_type: json.get("event_type").and_then(|v| v.as_str()).unwrap_or("raw").to_string(),
            payload: json.get("payload").cloned().unwrap_or(Value::Object(Default::default())),
            timestamp: json.get("timestamp").and_then(|v| v.as_i64()).unwrap_or_else(|| {
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_millis() as i64
            }),
        }
    }

    /// Create raw event from unparseable line
    pub fn raw_text(line: &str) -> Self {
        Self {
            version: "1.0".to_string(),
            actor: "system".to_string(),
            event_type: "raw".to_string(),
            payload: serde_json::json!({"text": line}),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis() as i64,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_event_from_valid_json() {
        let json = serde_json::json!({
            "version": "1.0",
            "actor": "daemon",
            "event_type": "state",
            "payload": {"daemon_running": true},
            "timestamp": 1709707200i64
        });

        let event = Event::from_json(json);
        assert_eq!(event.actor, "daemon");
        assert_eq!(event.event_type, "state");
        assert_eq!(event.timestamp, 1709707200);
    }

    #[test]
    fn test_event_raw_text() {
        let event = Event::raw_text("some unparseable text");
        assert_eq!(event.event_type, "raw");
        assert_eq!(event.actor, "system");
    }

    #[test]
    fn test_event_defaults() {
        let json = serde_json::json!({});
        let event = Event::from_json(json);
        assert_eq!(event.version, "1.0");
        assert_eq!(event.actor, "unknown");
        assert_eq!(event.event_type, "raw");
    }
}
