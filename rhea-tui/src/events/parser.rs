use super::event::Event;
use std::io::BufRead;

/// Parse a single line into an Event.
/// Never breaks the stream: if JSON parsing fails, wraps as raw event.
pub fn parse_event(line: &str) -> Event {
    match serde_json::from_str::<serde_json::Value>(line) {
        Ok(json) => Event::from_json(json),
        Err(_) => Event::raw_text(line),  // Never break: malformed → raw event
    }
}

/// Parse events from a BufRead source (e.g., file or stdin)
pub fn parse_events<R: BufRead>(reader: R) -> Vec<Event> {
    reader
        .lines()
        .filter_map(|line| line.ok())
        .filter(|line| !line.trim().is_empty())
        .map(|line| parse_event(&line))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_valid_json() {
        let json_line = r#"{"version":"1.0","actor":"daemon","event_type":"state","payload":{"running":true},"timestamp":1234567890}"#;
        let event = parse_event(json_line);
        
        assert_eq!(event.actor, "daemon");
        assert_eq!(event.event_type, "state");
        assert!(event.payload.get("running").map(|v| v.as_bool()).flatten().unwrap_or(false));
    }

    #[test]
    fn test_parse_malformed_json() {
        let bad_json = "this is not json at all";
        let event = parse_event(bad_json);
        
        // Should become raw event, never panic
        assert_eq!(event.event_type, "raw");
        assert_eq!(event.actor, "system");
    }

    #[test]
    fn test_parse_empty_object() {
        let json_line = "{}";
        let event = parse_event(json_line);
        
        // Should have defaults
        assert_eq!(event.version, "1.0");
        assert_eq!(event.actor, "unknown");
    }

    #[test]
    fn test_parse_partial_json() {
        let partial = r#"{"actor":"cli","event_type":"log"}"#;
        let event = parse_event(partial);
        
        assert_eq!(event.actor, "cli");
        assert_eq!(event.event_type, "log");
        assert_eq!(event.version, "1.0");  // default
    }

    #[test]
    fn test_stream_never_breaks() {
        let lines = vec![
            r#"{"actor":"daemon","event_type":"state","timestamp":1000}"#,
            "not json",
            r#"{"actor":"cli","event_type":"log","timestamp":2000}"#,
            "also not json",
        ];

        for line in lines {
            let event = parse_event(line);
            // Never panics, always produces Event
            assert!(!event.actor.is_empty());
            assert!(!event.event_type.is_empty());
        }
    }
}
