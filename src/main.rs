use axum::{
    extract::{Path, Json, State},
    http::StatusCode,
    routing::{get, post},
    Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Component {
    pub id: String,
    pub name: String,
    pub context_window: usize,
    pub priority: u8,
    pub cost_per_token: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenAllocation {
    pub prompt_id: String,
    pub allocations: Vec<(String, usize)>,
    pub total_tokens: usize,
    pub timestamp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AllocationRequest {
    pub prompt: String,
    pub total_budget: usize,
    pub components: Vec<String>,
}

type AppState = Arc<RwLock<(Vec<Component>, Vec<TokenAllocation>)>>;

#[tokio::main]
async fn main() {
    let state = Arc::new(RwLock::new((
        vec![
            Component {
                id: "biorenderer".to_string(),
                name: "BioRenderer".to_string(),
                context_window: 8192,
                priority: 9,
                cost_per_token: 0.001,
            },
            Component {
                id: "nodeeditor".to_string(),
                name: "NodeEditor".to_string(),
                context_window: 4096,
                priority: 8,
                cost_per_token: 0.0008,
            },
            Component {
                id: "governor".to_string(),
                name: "Governor".to_string(),
                context_window: 2048,
                priority: 7,
                cost_per_token: 0.0005,
            },
            Component {
                id: "teamchat".to_string(),
                name: "TeamChat".to_string(),
                context_window: 2048,
                priority: 6,
                cost_per_token: 0.0005,
            },
        ],
        vec![],
    )));

    let app = Router::new()
        .route("/health", get(health))
        .route("/components", get(list_components))
        .route("/components/:id", get(get_component))
        .route("/allocate", post(allocate_tokens))
        .route("/allocation/:id", get(get_allocation))
        .route("/allocations", get(list_allocations))
        .route("/forecast", post(forecast_usage))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3006")
        .await
        .unwrap();

    println!("🎬 Play Token Mapper running on http://127.0.0.1:3006");
    println!("   BioRenderer (9) | NodeEditor (8) | Governor (7) | TeamChat (6)");
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> &'static str {
    "Play Token Mapper active"
}

async fn list_components(
    State(state): State<AppState>,
) -> Json<Vec<Component>> {
    let (components, _) = state.read().await.clone();
    Json(components)
}

async fn get_component(
    Path(id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<Component>, StatusCode> {
    let (components, _) = state.read().await;
    components
        .iter()
        .find(|c| c.id == id)
        .cloned()
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn allocate_tokens(
    State(state): State<AppState>,
    Json(req): Json<AllocationRequest>,
) -> (StatusCode, Json<serde_json::Value>) {
    let (components, _) = state.read().await;

    let mut allocations = vec![];
    let mut remaining = req.total_budget;

    let mut sorted: Vec<_> = req
        .components
        .iter()
        .filter_map(|cid| components.iter().find(|c| c.id == *cid))
        .collect();
    sorted.sort_by_key(|c| std::cmp::Reverse(c.priority));

    for component in sorted {
        let allocated = (remaining as f64 * (component.priority as f64 / 100.0)).max(1.0) as usize;
        let actual = allocated.min(component.context_window).min(remaining);
        allocations.push((component.id.clone(), actual));
        remaining = remaining.saturating_sub(actual);
    }

    (
        StatusCode::CREATED,
        Json(serde_json::json!({
            "allocations": allocations,
            "total_allocated": req.total_budget - remaining,
        })),
    )
}

async fn get_allocation(
    Path(id): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<TokenAllocation>, StatusCode> {
    let (_, allocations) = state.read().await;
    allocations
        .iter()
        .find(|a| a.prompt_id == id)
        .cloned()
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}

async fn list_allocations(
    State(state): State<AppState>,
) -> Json<Vec<TokenAllocation>> {
    let (_, allocations) = state.read().await;
    Json(allocations.clone())
}

async fn forecast_usage(
    State(state): State<AppState>,
    Json(req): Json<serde_json::Value>,
) -> Json<serde_json::Value> {
    let (components, _) = state.read().await;
    let daily_prompts = req["daily_prompts"].as_u64().unwrap_or(100) as usize;
    let avg_tokens = req["avg_tokens_per_prompt"].as_u64().unwrap_or(500) as usize;

    let total_daily = daily_prompts * avg_tokens;
    let total_cost: f64 = components
        .iter()
        .map(|c| (total_daily as f64 / components.len() as f64) * c.cost_per_token)
        .sum();

    Json(serde_json::json!({
        "daily_prompts": daily_prompts,
        "total_daily_tokens": total_daily,
        "estimated_daily_cost": format!("${:.2}", total_cost),
    }))
}
