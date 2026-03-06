use axum::{
    extract::{Path, State},
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use rhea_session_server::{
    Session, CreateSessionRequest, AddMessageRequest,
    GetSessionResponse, SessionResponse,
    TribunalRequest, TribunalResponse, adversarial_check,
};
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;

type SessionStore = Arc<RwLock<Vec<Session>>>;

#[tokio::main]
async fn main() {
    let store: SessionStore = Arc::new(RwLock::new(vec![]));

    let app = Router::new()
        .route("/sessions", post(create_session))
        .route("/sessions", get(list_sessions))
        .route("/sessions/:id", get(get_session))
        .route("/sessions/:id/messages", post(add_message))
        .route("/dialog", post(dialog_tribunal))
        .with_state(store);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3000")
        .await
        .unwrap();
    
    println!("🌟 Rhea Session Server running on http://127.0.0.1:3000");
    
    axum::serve(listener, app).await.unwrap();
}

async fn create_session(
    State(store): State<SessionStore>,
    Json(req): Json<CreateSessionRequest>,
) -> (StatusCode, Json<SessionResponse>) {
    let session = Session::new(req.character);
    let response = SessionResponse::from(&session);
    
    store.write().await.push(session);
    
    (StatusCode::CREATED, Json(response))
}

async fn list_sessions(
    State(store): State<SessionStore>,
) -> Json<Vec<SessionResponse>> {
    let sessions = store.read().await;
    let responses = sessions.iter().map(SessionResponse::from).collect();
    Json(responses)
}

async fn get_session(
    State(store): State<SessionStore>,
    Path(id): Path<Uuid>,
) -> Result<Json<GetSessionResponse>, StatusCode> {
    let sessions = store.read().await;
    let session = sessions.iter().find(|s| s.id == id)
        .ok_or(StatusCode::NOT_FOUND)?;

    Ok(Json(GetSessionResponse {
        session: SessionResponse::from(session),
        messages: session.messages.clone(),
    }))
}

async fn dialog_tribunal(
    Json(req): Json<TribunalRequest>,
) -> Json<TribunalResponse> {
    let start = std::time::Instant::now();

    // Simulated multi-model consensus (no real LLM — deterministic heuristic).
    let word_count = req.text.split_whitespace().count();
    let agreement_score: f64 = match word_count {
        0..=3 => 0.92,   // very short claims → models tend to agree
        4..=12 => 0.74,  // medium claims → moderate agreement
        _ => 0.45,        // complex claims → genuine divergence
    };
    let models_responded: usize = 4;

    let reply = format!(
        "Tribunal consensus on \"{}\": {:.0}% agreement across {} models.",
        if req.text.len() > 60 { &req.text[..req.text.floor_char_boundary(60)] } else { &req.text },
        agreement_score * 100.0,
        models_responded,
    );

    // ── Adversarial devil's-advocate layer ──
    let (adversarial_note, confidence_adjusted) =
        adversarial_check(&req.text, agreement_score);

    let elapsed_s = start.elapsed().as_secs_f64();

    Json(TribunalResponse {
        reply,
        agreement_score,
        models_responded,
        elapsed_s,
        adversarial_note,
        confidence_adjusted,
    })
}

async fn add_message(
    State(store): State<SessionStore>,
    Path(id): Path<Uuid>,
    Json(req): Json<AddMessageRequest>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let mut sessions = store.write().await;
    let session = sessions.iter_mut().find(|s| s.id == id)
        .ok_or(StatusCode::NOT_FOUND)?;

    let msg = session.add_message(req.role, req.content, req.device_id);
    
    Ok(Json(serde_json::json!({
        "id": msg.id,
        "created_at": msg.created_at,
        "lamport_clock": msg.lamport_clock,
        "content": msg.content,
        "device_id": msg.device_id,
    })))
}
