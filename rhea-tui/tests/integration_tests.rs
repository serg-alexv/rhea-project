use rhea_tui::{
    events::{parse_event, Event},
    state::{AppState, reduce},
};
use serde_json::json;

#[test]
fn test_full_pipeline_parse_reduce_state() {
    let json = json!({
        "version": "1.0",
        "actor": "daemon",
        "event_type": "state",
        "payload": {
            "daemon_running": true,
            "port": 4444,
            "log_streaming": true
        },
        "timestamp": 1000
    });

    let event = Event::from_json(json);
    let mut state = AppState::new();
    reduce(&mut state, &event);

    assert!(state.system.daemon_running);
    assert_eq!(state.system.daemon_port, 4444);
    assert!(state.system.log_streaming);
}

#[test]
fn test_full_pipeline_multiple_actors() {
    let mut state = AppState::new();

    for actor in &["daemon", "cli", "chrome", "ai"] {
        let mut event = Event::raw_text(&format!("event from {}", actor));
        event.actor = actor.to_string();
        reduce(&mut state, &event);
    }

    assert_eq!(state.actors.len(), 4);
}

#[test]
fn test_full_pipeline_malformed_recovery() {
    let mut state = AppState::new();

    let malformed = parse_event("not json at all");
    reduce(&mut state, &malformed);

    assert_eq!(state.events.len(), 1);
    assert_eq!(state.events[0].event_type, "raw");

    let valid = Event::from_json(json!({
        "actor": "test",
        "event_type": "state",
        "payload": {},
        "timestamp": 1000
    }));
    reduce(&mut state, &valid);

    assert_eq!(state.events.len(), 2);
}

#[test]
fn test_full_pipeline_event_history_capped() {
    let mut state = AppState::new();

    for i in 0..1050 {
        let mut event = Event::raw_text(&format!("event {}", i));
        event.timestamp = i as i64;
        reduce(&mut state, &event);
    }

    assert_eq!(state.events.len(), 1000);
}
