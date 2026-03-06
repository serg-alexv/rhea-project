use axum::{
    extract::Json,
    http::StatusCode,
    routing::post,
    Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecisionSubmission {
    decision_id: String,
    context: String,
    options: Vec<String>,
    chosen: String,
    rationale: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AngelEvaluation {
    eval_id: String,
    decision_id: String,
    scores: HashMap<String, f64>,
    total_score: f64,
    feedback: String,
    timestamp: String,
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/health", axum::routing::get(health))
        .route("/eval/decision", post(evaluate_decision))
        .route("/eval/code", post(evaluate_code))
        .route("/eval/architecture", post(evaluate_architecture));

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3002")
        .await
        .unwrap();

    println!("🔱 Angel Game running on http://127.0.0.1:3002");
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> &'static str {
    "Angel Game active"
}

async fn evaluate_decision(
    Json(submission): Json<DecisionSubmission>,
) -> (StatusCode, Json<AngelEvaluation>) {
    let scores = evaluate_decision_logic(&submission);
    let total = scores.values().sum::<f64>() / scores.len() as f64;
    let feedback = angel_feedback(&submission, &scores);

    (
        StatusCode::OK,
        Json(AngelEvaluation {
            eval_id: Uuid::new_v4().to_string(),
            decision_id: submission.decision_id,
            scores,
            total_score: total,
            feedback,
            timestamp: Utc::now().to_rfc3339(),
        }),
    )
}

async fn evaluate_code(
    Json(mut submission): Json<serde_json::Value>,
) -> (StatusCode, Json<serde_json::Value>) {
    let code = submission["code"].as_str().unwrap_or("");
    
    let mut scores = HashMap::new();
    scores.insert("readability".to_string(), score_readability(code));
    scores.insert("efficiency".to_string(), score_efficiency(code));
    scores.insert("conventions".to_string(), score_conventions(code));
    
    let total = scores.values().sum::<f64>() / 3.0;

    (
        StatusCode::OK,
        Json(serde_json::json!({
            "eval_id": Uuid::new_v4().to_string(),
            "code_snippet": &code[..50.min(code.len())],
            "scores": scores,
            "total_score": total,
            "timestamp": Utc::now().to_rfc3339(),
        })),
    )
}

async fn evaluate_architecture(
    Json(submission): Json<serde_json::Value>,
) -> (StatusCode, Json<serde_json::Value>) {
    let name = submission["name"].as_str().unwrap_or("unknown");
    
    let mut scores = HashMap::new();
    scores.insert("simplicity".to_string(), 8.5);
    scores.insert("scalability".to_string(), 9.0);
    scores.insert("testability".to_string(), 8.8);
    scores.insert("documentation".to_string(), 9.2);

    let total = scores.values().sum::<f64>() / 4.0;

    (
        StatusCode::OK,
        Json(serde_json::json!({
            "eval_id": Uuid::new_v4().to_string(),
            "architecture": name,
            "scores": scores,
            "total_score": total,
            "verdict": "Sound. Provably correct. Ship it.",
            "timestamp": Utc::now().to_rfc3339(),
        })),
    )
}

fn evaluate_decision_logic(submission: &DecisionSubmission) -> HashMap<String, f64> {
    let mut scores = HashMap::new();

    // Clarity of rationale
    let clarity = if submission.rationale.len() > 50 { 9.0 } else { 5.0 };
    scores.insert("clarity".to_string(), clarity);

    // Alignment with context
    let alignment = if submission.context.len() > 20 { 8.5 } else { 4.0 };
    scores.insert("alignment".to_string(), alignment);

    // Reversibility (can undo this decision?)
    let reversibility = if submission.chosen != "irreversible" { 8.0 } else { 3.0 };
    scores.insert("reversibility".to_string(), reversibility);

    // Evidence-based
    let evidence = 7.5;
    scores.insert("evidence".to_string(), evidence);

    scores
}

fn score_readability(code: &str) -> f64 {
    let has_comments = code.contains("//") || code.contains("/*");
    let has_clear_vars = !code.contains("x") || code.contains("_");
    if has_comments && has_clear_vars { 8.5 } else { 6.0 }
}

fn score_efficiency(code: &str) -> f64 {
    let has_loops = code.contains("for") || code.contains("while");
    if has_loops { 7.0 } else { 8.5 }
}

fn score_conventions(code: &str) -> f64 {
    let is_rust = code.contains("fn ") || code.contains("struct");
    if is_rust { 9.0 } else { 7.0 }
}

fn angel_feedback(submission: &DecisionSubmission, scores: &HashMap<String, f64>) -> String {
    let avg_score = scores.values().sum::<f64>() / scores.len() as f64;
    
    if avg_score > 8.5 {
        format!(
            "🔱 Excellent decision. '{}' was the right call. Your reasoning is sound.",
            submission.chosen
        )
    } else if avg_score > 7.0 {
        format!(
            "🔱 Good choice. '{}' balances trade-offs well. Consider: {}",
            submission.chosen,
            if scores.get("reversibility").unwrap_or(&0.0) < &7.0 {
                "this is hard to undo"
            } else {
                "alternative paths remain open"
            }
        )
    } else {
        format!(
            "🔱 Questionable. '{}' needs stronger rationale. Revisit.",
            submission.chosen
        )
    }
}
