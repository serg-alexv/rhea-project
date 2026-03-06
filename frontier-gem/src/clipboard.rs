//! Clipboard monitoring — polls system clipboard, detects sensitive content, relays to server.

use arboard::Clipboard;
use regex::Regex;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::sync::LazyLock;
use tokio::sync::broadcast;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClipboardEvent {
    pub content: String,
    pub content_hash: String,
    pub content_type: String,
    pub sensitivity: Option<String>,
    pub ttl_seconds: Option<u64>,
    pub device_id: String,
    pub device_name: String,
    pub timestamp: String,
}

// Ported from packages/rhea-clipboard/src/rhea_clipboard/config.py SENSITIVE_PATTERNS
static SENSITIVITY_PATTERNS: LazyLock<Vec<(Regex, &'static str, u64)>> = LazyLock::new(|| {
    vec![
        (Regex::new(r"(?:sk|pk|ak|rk|token)[_-][A-Za-z0-9]{20,}").expect("hardcoded regex"), "api_key", 300),
        (Regex::new(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}").expect("hardcoded regex"), "github_token", 300),
        (Regex::new(r"(?:AKIA|ASIA)[A-Z0-9]{16}").expect("hardcoded regex"), "aws_key", 300),
        (Regex::new(r"(?:eyJ)[A-Za-z0-9_-]{20,}\.(?:eyJ)[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+").expect("hardcoded regex"), "jwt", 300),
        (Regex::new(r"\b(?:password|passwd|pwd)\s*[:=]\s*\S+").expect("hardcoded regex"), "password", 300),
        (Regex::new(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b").expect("hardcoded regex"), "credit_card", 300),
        (Regex::new(r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----").expect("hardcoded regex"), "private_key", 300),
        (Regex::new(r"(?:ssh-rsa|ssh-ed25519|ecdsa-sha2)\s+[A-Za-z0-9+/=]{40,}").expect("hardcoded regex"), "ssh_key", 300),
    ]
});

/// Returns (sensitivity_type, ttl_seconds) if content matches a known sensitive pattern.
pub fn detect_sensitivity(content: &str) -> Option<(String, u64)> {
    for (re, label, ttl) in SENSITIVITY_PATTERNS.iter() {
        if re.is_match(content) {
            return Some((label.to_string(), *ttl));
        }
    }
    None
}

pub fn detect_content_type(content: &str) -> String {
    if content.starts_with("http://") || content.starts_with("https://") {
        "url".to_string()
    } else if content.contains("fn ")
        || content.contains("def ")
        || content.contains("func ")
        || content.contains("function ")
    {
        "code".to_string()
    } else {
        "text".to_string()
    }
}

fn sha256_hex(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    hex::encode(hasher.finalize())
}

fn resolve_device_name() -> String {
    hostname::get()
        .ok()
        .and_then(|h| h.into_string().ok())
        .unwrap_or_else(|| "unknown".to_string())
}

/// POST clipboard event to relay server. Logs warning on failure — never panics.
async fn push_to_server(
    client: &Client,
    event: &ClipboardEvent,
    server_url: &str,
    auth_token: &Option<String>,
) {
    let url = format!("{}/clipboard", server_url.trim_end_matches('/'));
    let mut req = client.post(&url).json(event);
    if let Some(token) = auth_token {
        req = req.header("Authorization", format!("Bearer {}", token));
    }
    match req.send().await {
        Ok(resp) if !resp.status().is_success() => {
            eprintln!("⚠ clipboard relay: server returned {}", resp.status());
        }
        Err(e) => {
            eprintln!("⚠ clipboard relay unreachable: {}", e);
        }
        _ => {}
    }
}

/// Async monitor loop — polls clipboard every 500ms, broadcasts changes and relays to server.
///
/// Mirrors the Python `ClipboardMonitor._poll_loop` from rhea-clipboard:
/// - SHA256 dedup (skip unchanged)
/// - Sensitivity detection with TTL
/// - Broadcast via tokio channel
/// - POST to relay server
pub async fn clipboard_monitor(
    server_url: String,
    auth_token: Option<String>,
    tx: broadcast::Sender<ClipboardEvent>,
) {
    let device_id = uuid::Uuid::new_v4().to_string();
    let device_name = resolve_device_name();
    let client = Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .unwrap_or_default();

    let mut clipboard = match Clipboard::new() {
        Ok(c) => c,
        Err(e) => {
            eprintln!("✖ clipboard init failed: {}", e);
            return;
        }
    };

    // Seed with current clipboard content to avoid firing on startup
    let mut last_hash = clipboard
        .get_text()
        .map(|t| sha256_hex(&t))
        .unwrap_or_default();

    let mut interval = tokio::time::interval(std::time::Duration::from_millis(500));

    loop {
        interval.tick().await;

        let content = match clipboard.get_text() {
            Ok(c) => c,
            Err(_) => continue,
        };

        if content.trim().is_empty() {
            continue;
        }

        let hash = sha256_hex(&content);
        if hash == last_hash {
            continue;
        }
        last_hash = hash.clone();

        let (sensitivity, ttl) = match detect_sensitivity(&content) {
            Some((s, t)) => (Some(s), Some(t)),
            None => (None, None),
        };

        let event = ClipboardEvent {
            content: content.clone(),
            content_hash: hash,
            content_type: detect_content_type(&content),
            sensitivity,
            ttl_seconds: ttl,
            device_id: device_id.clone(),
            device_name: device_name.clone(),
            timestamp: chrono::Utc::now().to_rfc3339(),
        };

        let _ = tx.send(event.clone());
        push_to_server(&client, &event, &server_url, &auth_token).await;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_detect_sensitivity_api_key() {
        let (label, ttl) = detect_sensitivity("token-abcdefghijklmnopqrstuvwxyz1234567890").unwrap();
        assert_eq!(label, "api_key");
        assert_eq!(ttl, 300);
    }

    #[test]
    fn test_detect_sensitivity_github_token() {
        let (label, _) = detect_sensitivity("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn").unwrap();
        assert_eq!(label, "github_token");
    }

    #[test]
    fn test_detect_sensitivity_jwt() {
        let jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U";
        let (label, _) = detect_sensitivity(jwt).unwrap();
        assert_eq!(label, "jwt");
    }

    #[test]
    fn test_detect_sensitivity_none() {
        assert!(detect_sensitivity("hello world").is_none());
    }

    #[test]
    fn test_content_type_url() {
        assert_eq!(detect_content_type("https://example.com"), "url");
    }

    #[test]
    fn test_content_type_code() {
        assert_eq!(detect_content_type("fn main() {}"), "code");
        assert_eq!(detect_content_type("def foo():"), "code");
    }

    #[test]
    fn test_content_type_text() {
        assert_eq!(detect_content_type("just some text"), "text");
    }

    #[test]
    fn test_sha256_deterministic() {
        let a = sha256_hex("hello");
        let b = sha256_hex("hello");
        assert_eq!(a, b);
        assert_ne!(a, sha256_hex("world"));
    }
}
