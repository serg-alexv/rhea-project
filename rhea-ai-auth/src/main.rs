use axum::{
    extract::{Json, State},
    routing::{get, post},
    http::StatusCode,
    Router,
};
use serde::{Deserialize, Serialize};
use sha2::{Sha256, Digest};
use std::sync::Arc;
use uuid::Uuid;
use std::collections::HashMap;
use tokio::sync::Mutex;

#[derive(Clone, Serialize, Deserialize)]
struct Challenge {
    id: String,
    target_hash: String,
    code_template: String,
    created_at: i64,
}

#[derive(Serialize, Deserialize)]
struct ChallengeResponse {
    challenge_id: String,
    target_hash: String,
    code_template: String,
    instructions: String,
}

#[derive(Deserialize)]
struct VerifyRequest {
    challenge_id: String,
    code: String,
}

#[derive(Serialize)]
struct VerifyResponse {
    success: bool,
    message: String,
    token: Option<String>,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    service: String,
}

struct AppState {
    challenges: Arc<Mutex<HashMap<String, Challenge>>>,
    tokens: Arc<Mutex<Vec<String>>>,
}

#[tokio::main]
async fn main() {
    let state = AppState {
        challenges: Arc::new(Mutex::new(HashMap::new())),
        tokens: Arc::new(Mutex::new(Vec::new())),
    };

    let app = Router::new()
        .route("/health", get(health))
        .route("/auth/challenge", post(get_challenge))
        .route("/auth/verify", post(verify_challenge))
        .with_state(Arc::new(state));

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3001")
        .await
        .unwrap();
    
    println!("🔐 Rhea AI Auth service running on http://127.0.0.1:3001");
    println!("   POST /auth/challenge  — Get new challenge");
    println!("   POST /auth/verify     — Submit solution");

    axum::serve(listener, app).await.unwrap();
}

async fn health() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_string(),
        service: "rhea-ai-auth".to_string(),
    })
}

async fn get_challenge(
    State(state): State<Arc<AppState>>,
) -> Json<ChallengeResponse> {
    let challenge_id = Uuid::new_v4().to_string();
    
    let target_hash = format!("{:x}", Sha256::digest(b"AI_AUTH_2026"));
    
    let code_template = r#"
// Modify this code to output a string whose SHA256 hash matches the target.
// Target hash: [TARGET_HASH]
// 
// AI should be able to reverse-engineer this or use reasoning.
// Humans cannot.

fn solve() -> String {
    "modify_this".to_string()
}
"#.replace("[TARGET_HASH]", &target_hash);

    let challenge = Challenge {
        id: challenge_id.clone(),
        target_hash: target_hash.clone(),
        code_template: code_template.clone(),
        created_at: chrono::Utc::now().timestamp(),
    };

    let mut challenges = state.challenges.lock().await;
    challenges.insert(challenge_id.clone(), challenge);

    Json(ChallengeResponse {
        challenge_id,
        target_hash,
        code_template,
        instructions: "Modify code to output a string matching the hash. AI-solvable, human-proof.".to_string(),
    })
}

async fn verify_challenge(
    State(state): State<Arc<AppState>>,
    Json(req): Json<VerifyRequest>,
) -> (StatusCode, Json<VerifyResponse>) {
    let challenges = state.challenges.lock().await;
    
    let Some(challenge) = challenges.get(&req.challenge_id) else {
        return (StatusCode::NOT_FOUND, Json(VerifyResponse {
            success: false,
            message: "Challenge not found".to_string(),
            token: None,
        }));
    };

    let output = extract_code_output(&req.code);
    
    let mut hasher = Sha256::new();
    hasher.update(output.as_bytes());
    let result_hash = format!("{:x}", hasher.finalize());

    if result_hash == challenge.target_hash {
        let token = Uuid::new_v4().to_string();
        let mut tokens = state.tokens.lock().await;
        tokens.push(token.clone());

        (StatusCode::OK, Json(VerifyResponse {
            success: true,
            message: "✓ AI authenticated!".to_string(),
            token: Some(token),
        }))
    } else {
        (StatusCode::BAD_REQUEST, Json(VerifyResponse {
            success: false,
            message: format!("Hash mismatch. Expected: {}, got: {}", challenge.target_hash, result_hash),
            token: None,
        }))
    }
}

fn extract_code_output(code: &str) -> String {
    if let Some(start) = code.find('"') {
        if let Some(end) = code[start+1..].find('"') {
            return code[start+1..start+1+end].to_string();
        }
    }
    "unknown".to_string()
}
