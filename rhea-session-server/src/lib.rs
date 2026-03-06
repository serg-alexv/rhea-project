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

#[derive(Clone, Debug, Serialize, Deserialize, Eq, PartialEq)]
pub struct Message {
    pub id: Uuid,
    pub session_id: Uuid,
    pub role: String,
    pub content: String,
    pub created_at: i64,
    pub device_id: String,
    pub lamport_clock: u64,
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

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Session {
    pub id: Uuid,
    pub character: Character,
    pub title: String,
    pub messages: Vec<Message>,
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
            title: format!("Session {}", character.symbol()),
            messages: vec![],
            created_at: now,
            updated_at: now,
            client_id: None,
        }
    }

    pub fn add_message(&mut self, role: String, content: String, device_id: String) -> Message {
        let lc = self.messages.last().map(|m| m.lamport_clock).unwrap_or(0) + 1;
        let msg = Message::new(self.id, role, content, device_id, lc);
        self.messages.push(msg.clone());
        self.updated_at = Utc::now();
        msg
    }
}

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

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SessionResponse {
    pub id: Uuid,
    pub character: String,
    pub title: String,
    pub message_count: usize,
    pub lamport_clock: u64,
    pub created_at: DateTime<Utc>,
}

impl From<&Session> for SessionResponse {
    fn from(s: &Session) -> Self {
        SessionResponse {
            id: s.id,
            character: s.character.name().to_string(),
            title: s.title.clone(),
            message_count: s.messages.len(),
            lamport_clock: s.messages.last().map(|m| m.lamport_clock).unwrap_or(0),
            created_at: s.created_at,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GetSessionResponse {
    pub session: SessionResponse,
    pub messages: Vec<Message>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct KeystrokeEvent {
    pub id: String,
    pub session_id: Uuid,
    pub device_id: String,
    pub key: String,
    pub timestamp: i64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SessionWithKeystrokes {
    pub id: Uuid,
    pub character: String,
    pub messages: Vec<Message>,
    pub keystrokes: Vec<KeystrokeEvent>,
}

// ── Tribunal types ──────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
pub struct TribunalRequest {
    pub text: String,
    pub sender: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TribunalResponse {
    pub reply: String,
    pub agreement_score: f64,
    pub models_responded: usize,
    pub elapsed_s: f64,
    /// Devil's-advocate counter-argument added by the adversarial layer.
    pub adversarial_note: String,
    /// Original confidence discounted by the skepticism factor (×0.85).
    pub confidence_adjusted: f64,
}

/// Structured adversarial analysis applied after consensus.
pub fn adversarial_check(claim: &str, agreement_score: f64) -> (String, f64) {
    let note = if agreement_score > 0.8 {
        format!(
            "High agreement ({:.0}%) may indicate groupthink. \
             Consider: what evidence would *disprove* \"{}\"?",
            agreement_score * 100.0,
            truncate_claim(claim, 80),
        )
    } else if agreement_score < 0.5 {
        format!(
            "Low agreement ({:.0}%) suggests genuine ambiguity. \
             Multiple valid perspectives exist on \"{}\".",
            agreement_score * 100.0,
            truncate_claim(claim, 80),
        )
    } else {
        format!(
            "Moderate agreement ({:.0}%). \
             The claim \"{}\" warrants further evidence before full endorsement.",
            agreement_score * 100.0,
            truncate_claim(claim, 80),
        )
    };

    let confidence_adjusted = agreement_score * 0.85; // 15 % skepticism discount
    (note, confidence_adjusted)
}

fn truncate_claim(s: &str, max: usize) -> String {
    if s.len() <= max {
        s.to_string()
    } else {
        format!("{}…", &s[..s.floor_char_boundary(max)])
    }
}
