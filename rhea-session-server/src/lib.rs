use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum Character {
    Protos,
    Zerg,
    Terran,
    Aeon,
}

impl Character {
    pub fn symbol(&self) -> &str {
        match self {
            Character::Protos => "⚙️",
            Character::Zerg => "🧬",
            Character::Terran => "🔧",
            Character::Aeon => "✨",
        }
    }

    pub fn name(&self) -> &str {
        match self {
            Character::Protos => "PROTOS",
            Character::Zerg => "ZERG",
            Character::Terran => "TERRAN",
            Character::Aeon => "AEON",
        }
    }
}

/// Immutable event: never changes once created
#[derive(Clone, Debug, Serialize, Deserialize, Eq, PartialEq)]
pub struct Message {
    pub id: Uuid,                    // Immutable: unique forever
    pub session_id: Uuid,            // Immutable: never changes
    pub role: String,                // Immutable: who said it
    pub content: String,             // Immutable: what was said
    pub created_at: i64,             // Immutable: wall-clock timestamp
    pub device_id: String,           // Immutable: which device
    pub lamport_clock: u64,          // Immutable: causal order
}

impl Message {
    pub fn new(
        session_id: Uuid,
        role: String,
        content: String,
        device_id: String,
        lamport_clock: u64,
    ) -> Self {
        Message {
            id: Uuid::new_v4(),
            session_id,
            role,
            content,
            created_at: Utc::now().timestamp(),
            device_id,
            lamport_clock,
        }
    }
}

/// Session state (derived from messages, not stored)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Session {
    pub id: Uuid,
    pub character: Character,
    pub title: String,
    pub messages: Vec<Message>,  // Append-only immutable list
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub client_id: Option<String>,
}

impl Session {
    pub fn new(character: Character) -> Self {
        let now = Utc::now();
        Session {
            id: Uuid::new_v4(),
            character: character.clone(),
            title: format!("{} session", character.name()),
            messages: vec![],
            created_at: now,
            updated_at: now,
            client_id: None,
        }
    }

    /// Add message with automatic Lamport clock increment
    pub fn add_message(&mut self, role: String, content: String, device_id: String) -> Message {
        let lamport = if self.messages.is_empty() {
            1
        } else {
            self.messages.iter().map(|m| m.lamport_clock).max().unwrap_or(0) + 1
        };

        let msg = Message::new(
            self.id,
            role,
            content,
            device_id,
            lamport,
        );

        self.messages.push(msg.clone());
        self.updated_at = Utc::now();
        msg
    }

    /// Merge messages from another device (idempotent)
    pub fn merge_messages(&mut self, new_messages: Vec<Message>) {
        for msg in new_messages {
            // UUID dedup: only add if not already present
            if !self.messages.iter().any(|m| m.id == msg.id) {
                self.messages.push(msg);
            }
        }

        // Re-sort by Lamport clock to maintain causal order
        self.messages.sort_by_key(|m| m.lamport_clock);
        self.updated_at = Utc::now();
    }

    /// Rebuild session state from events (for verification)
    pub fn rebuild_from_events(id: Uuid, character: Character, messages: Vec<Message>) -> Self {
        let mut session = Session::new(character);
        session.id = id;
        session.messages = messages;
        session.messages.sort_by_key(|m| m.lamport_clock);
        session
    }

    pub fn last_n_messages(&self, n: usize) -> Vec<&Message> {
        self.messages
            .iter()
            .rev()
            .take(n)
            .rev()
            .collect()
    }
}

// API DTOs
#[derive(Debug, Serialize, Deserialize)]
pub struct CreateSessionRequest {
    pub character: Character,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AddMessageRequest {
    pub role: String,
    pub content: String,
    pub device_id: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SessionResponse {
    pub id: Uuid,
    pub character: Character,
    pub title: String,
    pub message_count: usize,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl From<&Session> for SessionResponse {
    fn from(s: &Session) -> Self {
        SessionResponse {
            id: s.id,
            character: s.character.clone(),
            title: s.title.clone(),
            message_count: s.messages.len(),
            created_at: s.created_at,
            updated_at: s.updated_at,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GetSessionResponse {
    pub session: SessionResponse,
    pub messages: Vec<Message>,
}
