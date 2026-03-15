mod clipboard;
#[cfg(target_os = "windows")]
mod clipboard_win;

use axum::{
    extract::{Json, Path, State},
    http::StatusCode,
    routing::{delete, get, post},
    Router,
};
use clipboard::ClipboardEntry;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;

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

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Node {
    pub id: String,
    pub label: String,
    pub x: Option<f32>,
    pub y: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Edge {
    pub from: String,
    pub to: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathwayRequest {
    pub nodes: Vec<Node>,
    pub edges: Vec<Edge>,
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

// Figure generation endpoints
async fn generate_molecule(
    Json(_req): Json<serde_json::Value>,
) -> (StatusCode, Json<serde_json::Value>) {
    (
        StatusCode::OK,
        Json(serde_json::json!({
            "type": "svg",
            "data": "<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><circle cx='50' cy='50' r='40' stroke='black' stroke-width='3' fill='red' /></svg>",
        })),
    )
}

async fn generate_pathway(
    Json(req): Json<PathwayRequest>,
) -> (StatusCode, Json<serde_json::Value>) {
    use svg::node::element::{Line, Rectangle, Text as SvgText};

    let mut document = svg::Document::new()
        .set("viewBox", (0, 0, 800, 600))
        .set("width", 800)
        .set("height", 600);

    // Simple deterministic layout: Grid-like if coords are missing
    let mut layout_nodes = req.nodes.clone();
    for (i, node) in layout_nodes.iter_mut().enumerate() {
        if node.x.is_none() || node.y.is_none() {
            node.x = Some(100.0 + (i as f32 % 4.0) * 150.0);
            node.y = Some(100.0 + (i as f32 / 4.0).floor() * 100.0);
        }
    }

    // Draw Edges
    for edge in &req.edges {
        let from_node = layout_nodes.iter().find(|n| n.id == edge.from);
        let to_node = layout_nodes.iter().find(|n| n.id == edge.to);

        if let (Some(f), Some(t)) = (from_node, to_node) {
            let line = Line::new()
                .set("x1", f.x.unwrap())
                .set("y1", f.y.unwrap())
                .set("x2", t.x.unwrap())
                .set("y2", t.y.unwrap())
                .set("stroke", "#555")
                .set("stroke-width", 2);
            document = document.add(line);
        }
    }

    // Draw Nodes
    for node in &layout_nodes {
        let x = node.x.unwrap();
        let y = node.y.unwrap();

        // Node Box
        let rect = Rectangle::new()
            .set("x", x - 40.0)
            .set("y", y - 15.0)
            .set("width", 80)
            .set("height", 30)
            .set("rx", 5)
            .set("fill", "#e1f5fe")
            .set("stroke", "#01579b")
            .set("stroke-width", 1);

        let label = SvgText::new(node.label.clone())
            .set("x", x)
            .set("y", y + 5.0)
            .set("text-anchor", "middle")
            .set("font-family", "monospace")
            .set("font-size", 12)
            .set("fill", "#01579b");

        document = document.add(rect).add(label);
    }

    (
        StatusCode::OK,
        Json(serde_json::json!({
            "type": "svg",
            "data": document.to_string(),
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
            "data": "<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><rect width='100' height='100' fill='blue' /></svg>",
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
