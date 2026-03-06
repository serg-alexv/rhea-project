mod clipboard;

use axum::{
    extract::{Path, Json, State},
    http::StatusCode,
    routing::{get, post, delete},
    Router,
};
use clipboard::ClipboardEntry;
use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PasteRequest {
    pub content_type: String,
    pub data: String,
    pub metadata: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CopyRequest {
    pub device_id: String,
    pub content_type: String,
    pub data: String,
}

type ClipboardStore = Arc<RwLock<Vec<ClipboardEntry>>>;

#[tokio::main]
async fn main() {
    let clipboard: ClipboardStore = Arc::new(RwLock::new(vec![]));

    let app = Router::new()
        .route("/health", get(health))
        .route("/copy/:session_id", post(copy_to_clipboard))
        .route("/paste/:session_id", get(paste_from_clipboard))
        .route("/paste/:session_id/latest", get(latest_from_clipboard))
        .route("/clipboard/:session_id", get(list_clipboard))
        .route("/clipboard/:session_id/:entry_id", delete(clear_entry))
        .route("/generate/molecule", post(generate_molecule))
        .route("/generate/pathway", post(generate_pathway))
        .route("/generate/crdt", post(generate_crdt))
        .route("/generate/paper", post(generate_paper))
        .with_state(clipboard);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3003")
        .await
        .unwrap();

    println!("🧬 BioRenderer + Clipboard running on http://127.0.0.1:3003");
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> &'static str {
    "BioRenderer active"
}

async fn copy_to_clipboard(
    Path(session_id): Path<String>,
    State(store): State<ClipboardStore>,
    Json(req): Json<CopyRequest>,
) -> (StatusCode, Json<serde_json::Value>) {
    let entry = ClipboardEntry::new(
        session_id.clone(),
        req.device_id.clone(),
        req.content_type,
        req.data,
    );

    store.write().await.push(entry.clone());

    (
        StatusCode::CREATED,
        Json(serde_json::json!({
            "id": entry.id,
            "copied": true,
            "session_id": session_id,
            "device_id": req.device_id,
        })),
    )
}

async fn paste_from_clipboard(
    Path(session_id): Path<String>,
    State(store): State<ClipboardStore>,
) -> (StatusCode, Json<Vec<ClipboardEntry>>) {
    let entries = store.read().await;
    let active: Vec<ClipboardEntry> = entries
        .iter()
        .filter(|e| e.session_id == session_id && !e.is_expired())
        .cloned()
        .collect();

    (StatusCode::OK, Json(active))
}

async fn latest_from_clipboard(
    Path(session_id): Path<String>,
    State(store): State<ClipboardStore>,
) -> Result<(StatusCode, Json<ClipboardEntry>), StatusCode> {
    let entries = store.read().await;
    entries
        .iter()
        .filter(|e| e.session_id == session_id && !e.is_expired())
        .max_by_key(|e| e.created_at)
        .cloned()
        .map(|e| (StatusCode::OK, Json(e)))
        .ok_or(StatusCode::NOT_FOUND)
}

async fn list_clipboard(
    Path(session_id): Path<String>,
    State(store): State<ClipboardStore>,
) -> (StatusCode, Json<serde_json::Value>) {
    let entries = store.read().await;
    let active: Vec<&ClipboardEntry> = entries
        .iter()
        .filter(|e| e.session_id == session_id && !e.is_expired())
        .collect();

    (
        StatusCode::OK,
        Json(serde_json::json!({
            "session_id": session_id,
            "entries": active,
            "count": active.len(),
        })),
    )
}

async fn clear_entry(
    Path((session_id, entry_id)): Path<(String, String)>,
    State(store): State<ClipboardStore>,
) -> StatusCode {
    let mut entries = store.write().await;
    entries.retain(|e| !(e.session_id == session_id && e.id == entry_id));
    StatusCode::OK
}

// Figure generation endpoints (stubs for now)
async fn generate_molecule(
    Json(_req): Json<serde_json::Value>,
) -> (StatusCode, Json<serde_json::Value>) {
    (
        StatusCode::OK,
        Json(serde_json::json!({
            "type": "svg",
            "data": "<svg>...</svg>",
        })),
    )
}

async fn generate_pathway(
    Json(_req): Json<serde_json::Value>,
) -> (StatusCode, Json<serde_json::Value>) {
    (
        StatusCode::OK,
        Json(serde_json::json!({
            "type": "svg",
            "data": "<svg>...</svg>",
        })),
    )
}

async fn generate_crdt(
    Json(_req): Json<serde_json::Value>,
) -> (StatusCode, Json<serde_json::Value>) {
    (
        StatusCode::OK,
        Json(serde_json::json!({
            "type": "svg",
            "data": "<svg>...</svg>",
        })),
    )
}

async fn generate_paper(
    Json(_req): Json<serde_json::Value>,
) -> (StatusCode, Json<serde_json::Value>) {
    (
        StatusCode::OK,
        Json(serde_json::json!({
            "type": "pdf",
            "data": "%PDF-1.4...",
        })),
    )
}
