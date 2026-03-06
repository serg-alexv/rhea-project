use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::Utc;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClipboardEntry {
    pub id: String,
    pub session_id: String,
    pub device_id: String,
    pub content_type: String, // svg, png, pdf
    pub data: String,
    pub metadata: serde_json::Value,
    pub created_at: i64,
    pub ttl_seconds: i64,
}

impl ClipboardEntry {
    pub fn new(
        session_id: String,
        device_id: String,
        content_type: String,
        data: String,
    ) -> Self {
        ClipboardEntry {
            id: Uuid::new_v4().to_string(),
            session_id,
            device_id,
            content_type,
            data,
            metadata: serde_json::json!({}),
            created_at: Utc::now().timestamp(),
            ttl_seconds: 3600, // 1 hour default
        }
    }

    pub fn is_expired(&self) -> bool {
        let now = Utc::now().timestamp();
        now - self.created_at > self.ttl_seconds
    }
}
