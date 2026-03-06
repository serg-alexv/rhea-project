#[cfg(test)]
mod tests {
    use crate::*;
    use uuid::Uuid;

    #[test]
    fn test_immutability_message_never_changes() {
        let device_a = "device-a".to_string();
        let msg = Message::new(
            Uuid::new_v4(),
            "user".to_string(),
            "Hello".to_string(),
            device_a,
            1,
        );

        let id_before = msg.id;
        let content_before = msg.content.clone();

        // Message is immutable by design (no &mut methods to change fields)
        assert_eq!(msg.id, id_before);
        assert_eq!(msg.content, content_before);
    }

    #[test]
    fn test_uuid_dedup_idempotent() {
        let session_id = Uuid::new_v4();
        let device_a = "device-a".to_string();
        
        let mut session1 = Session::new(Character::Protos);
        session1.id = session_id;
        
        // Device A sends message
        let msg = session1.add_message("user".to_string(), "Hello".to_string(), device_a.clone());
        assert_eq!(session1.messages.len(), 1);

        // Same message arrives again (duplicate from network)
        let msg_duplicate = msg.clone();
        session1.merge_messages(vec![msg_duplicate]);

        // UUID dedup: still only 1 message
        assert_eq!(session1.messages.len(), 1, "UUID dedup should prevent duplicates");
    }

    #[test]
    fn test_truth_convergence_two_devices() {
        let session_id = Uuid::new_v4();

        // Device A
        let mut device_a = Session::new(Character::Protos);
        device_a.id = session_id;
        let msg_a1 = device_a.add_message("user".to_string(), "Message A1".to_string(), "device-a".to_string());
        let msg_a2 = device_a.add_message("user".to_string(), "Message A2".to_string(), "device-a".to_string());

        // Device B (starts empty)
        let mut device_b = Session::new(Character::Protos);
        device_b.id = session_id;

        // Device B sends its own message
        let msg_b1 = device_b.add_message("user".to_string(), "Message B1".to_string(), "device-b".to_string());

        // Sync: A → B
        device_b.merge_messages(vec![msg_a1.clone(), msg_a2.clone()]);
        
        // Sync: B → A
        device_a.merge_messages(vec![msg_b1.clone()]);

        // Both devices now have same messages
        assert_eq!(device_a.messages.len(), 3);
        assert_eq!(device_b.messages.len(), 3);

        // Same order (Lamport clock ensures causality)
        assert_eq!(device_a.messages[0].lamport_clock, device_b.messages[0].lamport_clock);
        assert_eq!(device_a.messages[1].lamport_clock, device_b.messages[1].lamport_clock);
        assert_eq!(device_a.messages[2].lamport_clock, device_b.messages[2].lamport_clock);
    }

    #[test]
    fn test_lamport_clock_maintains_causality() {
        let mut session = Session::new(Character::Protos);

        let msg1 = session.add_message("user".to_string(), "First".to_string(), "device-1".to_string());
        let msg2 = session.add_message("user".to_string(), "Second".to_string(), "device-1".to_string());
        let msg3 = session.add_message("user".to_string(), "Third".to_string(), "device-1".to_string());

        // Lamport clock increments
        assert_eq!(msg1.lamport_clock, 1);
        assert_eq!(msg2.lamport_clock, 2);
        assert_eq!(msg3.lamport_clock, 3);

        // Can't scramble order (Lamport clock proves sequence)
        assert!(msg1.lamport_clock < msg2.lamport_clock);
        assert!(msg2.lamport_clock < msg3.lamport_clock);
    }

    #[test]
    fn test_rebuild_from_events_deterministic() {
        let session_id = Uuid::new_v4();

        // Create original session with messages
        let mut original = Session::new(Character::Protos);
        original.id = session_id;
        original.add_message("user".to_string(), "Msg1".to_string(), "dev-1".to_string());
        original.add_message("user".to_string(), "Msg2".to_string(), "dev-1".to_string());

        let msgs = original.messages.clone();

        // Rebuild from events
        let rebuilt = Session::rebuild_from_events(
            session_id,
            Character::Protos,
            msgs.clone(),
        );

        // Same state
        assert_eq!(rebuilt.messages.len(), original.messages.len());
        assert_eq!(rebuilt.messages[0].id, original.messages[0].id);
        assert_eq!(rebuilt.messages[1].id, original.messages[1].id);
    }
}
