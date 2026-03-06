use serde::{Deserialize, Deserializer, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Serialize)]
pub enum Character {
    Protos,
    Zerg,
    Terran,
    Aeon,
}

impl<'de> Deserialize<'de> for Character {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where D: Deserializer<'de> {
        let s = String::deserialize(deserializer)?;
        Ok(Character::from_str(&s))
    }
}

impl Character {
    pub fn all() -> [Character; 4] {
        [Character::Protos, Character::Zerg, Character::Terran, Character::Aeon]
    }

    pub fn from_str(s: &str) -> Character {
        match s.to_uppercase().as_str() {
            "PROTOS" => Character::Protos,
            "ZERG" => Character::Zerg,
            "TERRAN" => Character::Terran,
            "AEON" => Character::Aeon,
            _ => Character::Protos,
        }
    }

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

    pub fn title(&self) -> &str {
        match self {
            Character::Protos => "The Analyst",
            Character::Zerg => "The Pragmatist",
            Character::Terran => "The Engineer",
            Character::Aeon => "The Visionary",
        }
    }

    pub fn description(&self) -> &str {
        match self {
            Character::Protos => "Sees patterns, optimizes architecture",
            Character::Zerg => "Fast decisions, just ship it",
            Character::Terran => "Been there, done that, hands-on",
            Character::Aeon => "Big picture, long-term thinking",
        }
    }

    pub fn thinking_phrase(&self) -> &str {
        match self {
            Character::Protos => "Logic trace in progress...",
            Character::Zerg => "Quick scan...",
            Character::Terran => "Checking experience...",
            Character::Aeon => "Exploring implications...",
        }
    }

    pub fn thinking_style(&self) -> &str {
        match self {
            Character::Protos => "Analysis",
            Character::Zerg => "Scan",
            Character::Terran => "Experience",
            Character::Aeon => "Vision",
        }
    }

    pub fn color(&self) -> ratatui::style::Color {
        use ratatui::style::Color;
        match self {
            Character::Protos => Color::Yellow,
            Character::Zerg => Color::Magenta,
            Character::Terran => Color::Red,
            Character::Aeon => Color::Cyan,
        }
    }
}

#[derive(Clone, Debug)]
pub struct Response {
    pub character: Character,
    pub thinking_started: bool,
    pub thinking_phase: String,
    pub alternatives: Vec<String>,
    pub main_response: String,
    pub thinking_complete: bool,
}

impl Response {
    pub fn new(character: Character) -> Self {
        Response {
            character,
            thinking_started: true,
            thinking_phase: character.thinking_style().to_string(),
            alternatives: vec![],
            main_response: String::new(),
            thinking_complete: false,
        }
    }

    pub fn add_thinking(&mut self, phase: String) {
        self.thinking_phase = phase;
    }

    pub fn add_alternative(&mut self, alt: String) {
        self.alternatives.push(alt);
    }

    pub fn set_answer(&mut self, answer: String) {
        self.main_response = answer;
        self.thinking_complete = true;
    }
}
