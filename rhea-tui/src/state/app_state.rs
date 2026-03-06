use crate::events::Event;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

/// Represents the status of a single actor (daemon, cli, chrome, ai, etc.)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ActorStatus {
    pub name: String,
    pub last_seen: i64,              // Unix timestamp ms
    pub status: String,              // "active", "idle", "error"
    pub event_count: u32,            // Total events from this actor
}

impl ActorStatus {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.to_string(),
            last_seen: current_timestamp(),
            status: "active".to_string(),
            event_count: 0,
        }
    }

    pub fn update_activity(&mut self) {
        self.last_seen = current_timestamp();
        self.event_count += 1;
    }
}

/// System-level status information
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SystemStatus {
    pub daemon_running: bool,
    pub daemon_port: u16,
    pub log_streaming: bool,
    pub timestamp: i64,
}

impl Default for SystemStatus {
    fn default() -> Self {
        Self {
            daemon_running: false,
            daemon_port: 0,
            log_streaming: false,
            timestamp: current_timestamp(),
        }
    }
}

/// Represents available AI nodes and their states
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DiscoveryNode {
    pub id: String,
    pub provider: String,
    pub model: String,
    pub status: String,              // "ready", "thinking", "busy", "offline"
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DiscoveryState {
    pub active_nodes: Vec<DiscoveryNode>,
    pub system_focus: String,        // Currently focused window/app
    pub timestamp: i64,
}

impl Default for DiscoveryState {
    fn default() -> Self {
        Self {
            active_nodes: Vec::new(),
            system_focus: "unknown".to_string(),
            timestamp: current_timestamp(),
        }
    }
}

/// Logic chain execution state
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LogicChainState {
    pub goal: String,
    pub sequence: Vec<String>,
    pub current_step: usize,
    pub timestamp: i64,
}

impl Default for LogicChainState {
    fn default() -> Self {
        Self {
            goal: String::new(),
            sequence: Vec::new(),
            current_step: 0,
            timestamp: current_timestamp(),
        }
    }
}

/// Single source of truth for cockpit state.
/// Represents the complete state of the system at any moment.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AppState {
    pub events: Vec<Event>,                         // Last N events
    pub actors: HashMap<String, ActorStatus>,      // All known actors
    pub system: SystemStatus,                      // System-level info
    pub discovery: DiscoveryState,                 // Available AI nodes
    pub logic_chain: LogicChainState,              // Active logic chain
}

impl AppState {
    pub fn new() -> Self {
        Self {
            events: Vec::new(),
            actors: HashMap::new(),
            system: SystemStatus::default(),
            discovery: DiscoveryState::default(),
            logic_chain: LogicChainState::default(),
        }
    }

    /// Add event to history, keeping last N events
    pub fn add_event(&mut self, event: Event) {
        self.events.push(event);
        if self.events.len() > 1000 {
            self.events.remove(0);
        }
    }

    /// Get or create actor, update its activity
    pub fn touch_actor(&mut self, actor: &str) {
        self.actors
            .entry(actor.to_string())
            .or_insert_with(|| ActorStatus::new(actor))
            .update_activity();
    }

    /// Get most recent N events
    pub fn recent_events(&self, n: usize) -> Vec<&Event> {
        self.events
            .iter()
            .rev()
            .take(n)
            .rev()
            .collect()
    }

    /// Get events from specific actor
    pub fn events_from_actor(&self, actor: &str) -> Vec<&Event> {
        self.events
            .iter()
            .filter(|e| e.actor == actor)
            .collect()
    }
}

impl Default for AppState {
    fn default() -> Self {
        Self::new()
    }
}

fn current_timestamp() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as i64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_app_state_new() {
        let state = AppState::new();
        assert!(state.events.is_empty());
        assert!(state.actors.is_empty());
        assert!(!state.system.daemon_running);
    }

    #[test]
    fn test_add_event() {
        let mut state = AppState::new();
        let event = Event::raw_text("test");
        state.add_event(event);
        assert_eq!(state.events.len(), 1);
    }

    #[test]
    fn test_touch_actor() {
        let mut state = AppState::new();
        state.touch_actor("daemon");
        state.touch_actor("daemon");

        let actor = state.actors.get("daemon").unwrap();
        assert_eq!(actor.name, "daemon");
        assert_eq!(actor.event_count, 2);
    }

    #[test]
    fn test_recent_events() {
        let mut state = AppState::new();
        for i in 0..5 {
            state.add_event(Event::raw_text(&format!("event {}", i)));
        }

        let recent = state.recent_events(3);
        assert_eq!(recent.len(), 3);
    }

    #[test]
    fn test_events_from_actor() {
        let mut state = AppState::new();
        for actor in &["daemon", "cli", "daemon"] {
            let mut evt = Event::raw_text("test");
            evt.actor = actor.to_string();
            state.add_event(evt);
        }

        let daemon_events = state.events_from_actor("daemon");
        assert_eq!(daemon_events.len(), 2);
    }

    #[test]
    fn test_event_history_trimmed() {
        let mut state = AppState::new();
        for i in 0..1001 {
            state.add_event(Event::raw_text(&format!("event {}", i)));
        }
        assert_eq!(state.events.len(), 1000);
    }

    #[test]
    fn test_actor_status_new() {
        let actor = ActorStatus::new("test");
        assert_eq!(actor.name, "test");
        assert_eq!(actor.status, "active");
        assert_eq!(actor.event_count, 0);
    }
}
