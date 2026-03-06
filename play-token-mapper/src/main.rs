use axum::{
    extract::{Path, Json, State},
    http::StatusCode,
    routing::{get, post, delete},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Component {
    pub id: String,
    pub name: String,
    pub priority: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateComponentRequest {
    pub id: String,
    pub name: String,
    pub priority: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AllocationRequest {
    pub budget: usize,
    pub components: Vec<String>,
}

type Store = Arc<RwLock<Vec<Component>>>;

#[tokio::main]
async fn main() {
    let store = Arc::new(RwLock::new(vec![
        Component { id: "bio".to_string(), name: "BioRenderer".to_string(), priority: 9 },
        Component { id: "node".to_string(), name: "NodeEditor".to_string(), priority: 8 },
        Component { id: "gov".to_string(), name: "Governor".to_string(), priority: 7 },
        Component { id: "chat".to_string(), name: "TeamChat".to_string(), priority: 6 },
    ]));

    let app = Router::new()
        .route("/health", get(health))
        .route("/components", get(list_components))
        .route("/components", post(create_component))
        .route("/components/:id", delete(delete_component))
        .route("/allocate", post(allocate))
        .with_state(store);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3006").await.unwrap();
    println!("🎬 Play Token Mapper (dynamic components) on http://127.0.0.1:3006");
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> &'static str {
    "OK"
}

async fn list_components(
    State(store): State<Store>,
) -> Json<Vec<Component>> {
    Json(store.read().await.clone())
}

async fn create_component(
    State(store): State<Store>,
    Json(req): Json<CreateComponentRequest>,
) -> (StatusCode, Json<Component>) {
    let comp = Component {
        id: req.id,
        name: req.name,
        priority: req.priority,
    };
    
    store.write().await.push(comp.clone());
    
    (StatusCode::CREATED, Json(comp))
}

async fn delete_component(
    Path(id): Path<String>,
    State(store): State<Store>,
) -> StatusCode {
    store.write().await.retain(|c| c.id != id);
    StatusCode::OK
}

async fn allocate(
    State(store): State<Store>,
    Json(req): Json<AllocationRequest>,
) -> Json<serde_json::Value> {
    let comps = store.read().await;
    let mut alloc = vec![];
    let mut remain = req.budget;

    let mut sorted: Vec<_> = req.components.iter()
        .filter_map(|id| comps.iter().find(|c| c.id == *id))
        .collect();
    sorted.sort_by_key(|c| std::cmp::Reverse(c.priority));

    for c in sorted {
        let amt = (remain as f64 * c.priority as f64 / 100.0).max(1.0) as usize;
        alloc.push((c.id.clone(), amt));
        remain = remain.saturating_sub(amt);
    }

    Json(serde_json::json!({ 
        "allocations": alloc,
        "total_allocated": req.budget - remain
    }))
}
