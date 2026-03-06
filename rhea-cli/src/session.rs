use crate::character::Character;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Message {
    pub role: String, // "user" or character name
    pub content: String,
    pub timestamp: i64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Session {
    pub id: String,
    pub character: Character,
    pub messages: Vec<Message>,
    pub created_at: i64,
    pub title: String,
}

impl Session {
    pub fn new(character: Character) -> Self {
        let now = Utc::now().timestamp();
        Session {
            id: format!("session_{}", now),
            character,
            messages: vec![],
            created_at: now,
            title: format!("{} session", character.name()),
        }
    }

    pub fn add_message(&mut self, content: String) {
        let now = Utc::now().timestamp();
        self.messages.push(Message {
            role: "user".to_string(),
            content: content.clone(),
            timestamp: now,
        });
        
        // Auto-generate response (mock for now)
        self.messages.push(Message {
            role: self.character.name().to_string(),
            content: self.generate_response(&content),
            timestamp: now + 1,
        });
    }

    pub fn generate_response(&self, user_input: &str) -> String {
        match self.character {
            crate::character::Character::Protos => {
                format!(
                    "⚙️ [Analyzing...]\n\nI see you're asking about: {}\n\nLet me think through the logic here...",
                    user_input
                )
            }
            crate::character::Character::Zerg => {
                format!("🧬 [Quick scan...]\n\nGot it. {}\n\nLet's move fast.", user_input)
            }
            crate::character::Character::Terran => {
                format!(
                    "🔧 [Experience check...]\n\nI've seen this before. {}\n\nHere's what worked...",
                    user_input
                )
            }
            crate::character::Character::Aeon => {
                format!(
                    "✨ [Vision explore...]\n\nInteresting question: {}\n\nLet me explore the implications...",
                    user_input
                )
            }
        }
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
