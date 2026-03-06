use axum::{
    extract::Json,
    http::StatusCode,
    routing::{get, post},
    Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RAGDocument {
    id: String,
    source: String,
    content: String,
    doc_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RAGQuery {
    query: String,
    doc_type: Option<String>,
    limit: Option<usize>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RAGResult {
    doc_id: String,
    source: String,
    content: String,
    relevance_score: f64,
    doc_type: String,
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/health", get(health))
        .route("/index/document", post(index_document))
        .route("/search", post(search_documents))
        .route("/search/by-type", post(search_by_type))
        .route("/context/decision", post(get_decision_context))
        .route("/context/architecture", post(get_architecture_context));

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3004")
        .await
        .unwrap();

    println!("🧠 RAG Storage running on http://127.0.0.1:3004");
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> &'static str {
    "RAG Storage active"
}

async fn index_document(
    Json(doc): Json<RAGDocument>,
) -> (StatusCode, Json<serde_json::Value>) {
    (
        StatusCode::CREATED,
        Json(serde_json::json!({
            "doc_id": doc.id,
            "source": doc.source,
            "indexed": true,
            "timestamp": Utc::now().to_rfc3339(),
        })),
    )
}

async fn search_documents(
    Json(query): Json<RAGQuery>,
) -> (StatusCode, Json<Vec<RAGResult>>) {
    let results = vec![
        RAGResult {
            doc_id: Uuid::new_v4().to_string(),
            source: "docs/decisions.md".to_string(),
            content: "ADR-017: Lamport Clocks ensure deterministic ordering across devices..."
                .to_string(),
            relevance_score: 0.95,
            doc_type: "architecture".to_string(),
        },
    ];

    (StatusCode::OK, Json(results))
}

async fn search_by_type(
    Json(_query): Json<RAGQuery>,
) -> (StatusCode, Json<Vec<RAGResult>>) {
    let results = vec![RAGResult {
        doc_id: "adr-017".to_string(),
        source: "docs/decisions.md".to_string(),
        content: "Lamport Clocks for DTS".to_string(),
        relevance_score: 0.92,
        doc_type: "architecture".to_string(),
    }];

    (StatusCode::OK, Json(results))
}

async fn get_decision_context(
    Json(req): Json<serde_json::Value>,
) -> (StatusCode, Json<serde_json::Value>) {
    let decision_id = req["decision_id"].as_str().unwrap_or("unknown");

    (
        StatusCode::OK,
        Json(serde_json::json!({
            "decision_id": decision_id,
            "architecture_refs": vec!["ADR-017", "ADR-015", "ADR-016"],
            "related_code": vec!["rhea-session-server/src/lib.rs", "rhea-client/src/lib.rs"],
            "task_history": vec!["stage4-dts-choice", "stage4-async-refactor"],
            "angel_game_scores": {
                "clarity": 9.0,
                "alignment": 8.5,
                "reversibility": 8.0,
                "evidence": 7.5,
            },
            "timestamp": Utc::now().to_rfc3339(),
        })),
    )
}

async fn get_architecture_context(
    Json(req): Json<serde_json::Value>,
) -> (StatusCode, Json<serde_json::Value>) {
    let arch_id = req["architecture_id"].as_str().unwrap_or("unknown");

    (
        StatusCode::OK,
        Json(serde_json::json!({
            "architecture_id": arch_id,
            "adrs": vec!["ADR-017", "ADR-015", "ADR-016"],
            "timestamp": Utc::now().to_rfc3339(),
        })),
    )
}
