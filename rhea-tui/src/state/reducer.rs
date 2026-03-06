use super::app_state::AppState;
use crate::events::Event;

/// Pure state reducer: (old_state + event) → new_state
/// No side effects, fully deterministic and testable.
pub fn reduce(state: &mut AppState, event: &Event) {
    // Add event to history
    state.add_event(event.clone());

    // Update actor activity
    state.touch_actor(&event.actor);

    // Process by event type
    match event.event_type.as_str() {
        // System state events
        "state" => reduce_state_event(state, event),
        
        // Discovery events (AI nodes)
        "discovery" => reduce_discovery_event(state, event),
        
        // Logic chain events
        "logic_chain" => reduce_logic_chain_event(state, event),
        
        // All others are just recorded
        _ => {}
    }
}

/// Process system state events (from daemon, typically)
fn reduce_state_event(state: &mut AppState, event: &Event) {
    if event.actor == "daemon" {
        if let Some(running) = event.payload.get("daemon_running").and_then(|v| v.as_bool()) {
            state.system.daemon_running = running;
        }
        if let Some(port) = event.payload.get("port").and_then(|v| v.as_u64()) {
            state.system.daemon_port = port as u16;
        }
        if let Some(streaming) = event.payload.get("log_streaming").and_then(|v| v.as_bool()) {
            state.system.log_streaming = streaming;
        }
        state.system.timestamp = event.timestamp;
    }
}

/// Process discovery events (available AI nodes)
fn reduce_discovery_event(state: &mut AppState, event: &Event) {
    if let Some(nodes) = event.payload.get("active_nodes").and_then(|v| v.as_array()) {
        state.discovery.active_nodes.clear();
        for node_json in nodes {
            if let Some(id) = node_json.get("id").and_then(|v| v.as_str()) {
                state.discovery.active_nodes.push(super::app_state::DiscoveryNode {
                    id: id.to_string(),
                    provider: node_json
                        .get("provider")
                        .and_then(|v| v.as_str())
                        .unwrap_or("unknown")
                        .to_string(),
                    model: node_json
                        .get("model")
                        .and_then(|v| v.as_str())
                        .unwrap_or("unknown")
                        .to_string(),
                    status: node_json
                        .get("status")
                        .and_then(|v| v.as_str())
                        .unwrap_or("unknown")
                        .to_string(),
                });
            }
        }
    }
    if let Some(focus) = event.payload.get("system_focus").and_then(|v| v.as_str()) {
        state.discovery.system_focus = focus.to_string();
    }
    state.discovery.timestamp = event.timestamp;
}

/// Process logic chain events
fn reduce_logic_chain_event(state: &mut AppState, event: &Event) {
    if let Some(goal) = event.payload.get("goal").and_then(|v| v.as_str()) {
        state.logic_chain.goal = goal.to_string();
    }
    if let Some(sequence) = event.payload.get("sequence").and_then(|v| v.as_array()) {
        state.logic_chain.sequence = sequence
            .iter()
            .filter_map(|step| step.as_str().map(|s| s.to_string()))
            .collect();
    }
    if let Some(step) = event.payload.get("current_step").and_then(|v| v.as_u64()) {
        state.logic_chain.current_step = step as usize;
    }
    state.logic_chain.timestamp = event.timestamp;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reduce_adds_event() {
        let mut state = AppState::new();
        let event = Event::raw_text("test");
        reduce(&mut state, &event);

        assert_eq!(state.events.len(), 1);
        assert_eq!(state.events[0].event_type, "raw");
    }

    #[test]
    fn test_reduce_touches_actor() {
        let mut state = AppState::new();
        let mut event = Event::raw_text("test");
        event.actor = "daemon".to_string();

        reduce(&mut state, &event);
        
        assert!(state.actors.contains_key("daemon"));
        let actor = state.actors.get("daemon").unwrap();
        assert_eq!(actor.event_count, 1);
    }

    #[test]
    fn test_reduce_daemon_state() {
        let mut state = AppState::new();
        let mut event = Event::raw_text("");
        event.actor = "daemon".to_string();
        event.event_type = "state".to_string();
        event.payload = serde_json::json!({
            "daemon_running": true,
            "port": 4444,
            "log_streaming": true
        });

        reduce(&mut state, &event);

        assert!(state.system.daemon_running);
        assert_eq!(state.system.daemon_port, 4444);
        assert!(state.system.log_streaming);
    }

    #[test]
    fn test_reduce_discovery_event() {
        let mut state = AppState::new();
        let mut event = Event::raw_text("");
        event.event_type = "discovery".to_string();
        event.payload = serde_json::json!({
            "active_nodes": [
                {"id": "node1", "provider": "anthropic", "model": "claude", "status": "ready"},
                {"id": "node2", "provider": "openai", "model": "gpt4", "status": "thinking"}
            ],
            "system_focus": "chrome.exe"
        });

        reduce(&mut state, &event);

        assert_eq!(state.discovery.active_nodes.len(), 2);
        assert_eq!(state.discovery.system_focus, "chrome.exe");
        assert_eq!(state.discovery.active_nodes[0].provider, "anthropic");
    }

    #[test]
    fn test_reduce_logic_chain_event() {
        let mut state = AppState::new();
        let mut event = Event::raw_text("");
        event.event_type = "logic_chain".to_string();
        event.payload = serde_json::json!({
            "goal": "solve_problem",
            "sequence": ["analyze", "plan", "execute"],
            "current_step": 1
        });

        reduce(&mut state, &event);

        assert_eq!(state.logic_chain.goal, "solve_problem");
        assert_eq!(state.logic_chain.sequence.len(), 3);
        assert_eq!(state.logic_chain.current_step, 1);
    }

    #[test]
    fn test_reduce_is_deterministic() {
        let mut state1 = AppState::new();
        let mut state2 = AppState::new();

        let event = serde_json::json!({
            "version": "1.0",
            "actor": "daemon",
            "event_type": "state",
            "payload": {"daemon_running": true, "port": 5000},
            "timestamp": 1234567890
        });
        let parsed = crate::events::Event::from_json(event);

        reduce(&mut state1, &parsed);
        reduce(&mut state2, &parsed);

        assert_eq!(state1.system.daemon_running, state2.system.daemon_running);
        assert_eq!(state1.system.daemon_port, state2.system.daemon_port);
        assert_eq!(state1.actors.len(), state2.actors.len());
    }
}
