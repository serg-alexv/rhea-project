use axum::{
    extract::Json,
    http::StatusCode,
    routing::post,
    Router,
};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoleculeRequest {
    name: String,
    smiles: Option<String>,
    description: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathwayRequest {
    name: String,
    steps: Vec<String>,
    organism: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaperFigure {
    figure_id: String,
    figure_type: String,
    title: String,
    caption: String,
    svg_data: String,
    timestamp: String,
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/health", axum::routing::get(health))
        .route("/generate/molecule", post(generate_molecule_figure))
        .route("/generate/pathway", post(generate_pathway_figure))
        .route("/generate/crdt", post(generate_crdt_figure))
        .route("/generate/paper", post(generate_paper_figures));

    let listener = tokio::net::TcpListener::bind("127.0.0.1:3003")
        .await
        .unwrap();

    println!("🧬 BioRenderer running on http://127.0.0.1:3003");
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> &'static str {
    "BioRenderer active"
}

async fn generate_molecule_figure(
    Json(req): Json<MoleculeRequest>,
) -> (StatusCode, Json<PaperFigure>) {
    let svg = format!(
        r#"<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="80" fill="none" stroke="#333" stroke-width="2"/>
        <text x="100" y="105" text-anchor="middle" font-size="16">{}</text>
        <text x="100" y="125" text-anchor="middle" font-size="12" fill="#666">{}</text>
        </svg>"#,
        req.name,
        req.smiles.as_deref().unwrap_or("No SMILES")
    );

    (
        StatusCode::CREATED,
        Json(PaperFigure {
            figure_id: Uuid::new_v4().to_string(),
            figure_type: "molecule".to_string(),
            title: format!("Structure of {}", req.name),
            caption: req
                .description
                .unwrap_or_else(|| format!("Molecular structure visualization")),
            svg_data: svg,
            timestamp: Utc::now().to_rfc3339(),
        }),
    )
}

async fn generate_pathway_figure(
    Json(req): Json<PathwayRequest>,
) -> (StatusCode, Json<PaperFigure>) {
    let steps_svg = req
        .steps
        .iter()
        .enumerate()
        .map(|(i, step)| {
            let x = 50 + i * 80;
            format!(
                r#"<rect x="{}" y="80" width="60" height="40" fill="#e8f4f8" stroke="#0088cc" stroke-width="2" rx="5"/>
                <text x="{}" y="105" text-anchor="middle" font-size="11">{}</text>"#,
                x, x + 30, step
            )
        })
        .collect::<Vec<_>>()
        .join("\n");

    let svg = format!(
        r#"<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg">
        <text x="10" y="25" font-size="14" font-weight="bold">{}</text>
        {}
        </svg>"#,
        req.name, steps_svg
    );

    (
        StatusCode::CREATED,
        Json(PaperFigure {
            figure_id: Uuid::new_v4().to_string(),
            figure_type: "pathway".to_string(),
            title: format!("Pathway: {}", req.name),
            caption: format!(
                "Biological pathway in {}",
                req.organism.as_deref().unwrap_or("organism")
            ),
            svg_data: svg,
            timestamp: Utc::now().to_rfc3339(),
        }),
    )
}

async fn generate_crdt_figure(
    Json(_req): Json<serde_json::Value>,
) -> (StatusCode, Json<PaperFigure>) {
    let svg = r#"<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
        <text x="200" y="25" text-anchor="middle" font-size="16" font-weight="bold">CRDT Convergence</text>
        
        <!-- Device A -->
        <rect x="20" y="60" width="140" height="100" fill="#fff5e6" stroke="#ff9933" stroke-width="2" rx="5"/>
        <text x="90" y="80" text-anchor="middle" font-weight="bold">Device A</text>
        <text x="30" y="110" font-size="11">Msg 1 (LC=1)</text>
        <text x="30" y="135" font-size="11">Msg 2 (LC=2)</text>
        
        <!-- Device B -->
        <rect x="240" y="60" width="140" height="100" fill="#e6f5ff" stroke="#0088cc" stroke-width="2" rx="5"/>
        <text x="310" y="80" text-anchor="middle" font-weight="bold">Device B</text>
        <text x="250" y="110" font-size="11">Msg 1 (LC=1)</text>
        <text x="250" y="135" font-size="11">Msg 2 (LC=2)</text>
        
        <!-- Convergence arrow -->
        <path d="M 160 210 Q 200 240 240 210" stroke="#22aa44" stroke-width="3" fill="none" marker-end="url(#arrowhead)"/>
        <text x="200" y="260" text-anchor="middle" font-weight="bold" fill="#22aa44">Same order on both</text>
        
        <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto">
                <polygon points="0 0, 10 5, 0 10" fill="#22aa44"/>
            </marker>
        </defs>
        </svg>"#.to_string();

    (
        StatusCode::CREATED,
        Json(PaperFigure {
            figure_id: Uuid::new_v4().to_string(),
            figure_type: "crdt".to_string(),
            title: "CRDT Message Ordering Convergence".to_string(),
            caption: "Lamport Clocks ensure deterministic ordering across distributed devices"
                .to_string(),
            svg_data: svg,
            timestamp: Utc::now().to_rfc3339(),
        }),
    )
}

async fn generate_paper_figures(
    Json(_req): Json<serde_json::Value>,
) -> (StatusCode, Json<Vec<PaperFigure>>) {
    let mut figures = vec![];

    // Figure 1: CRDT Convergence
    figures.push(PaperFigure {
        figure_id: Uuid::new_v4().to_string(),
        figure_type: "crdt".to_string(),
        title: "Figure 1: CRDT Deterministic Ordering".to_string(),
        caption: "Multi-device session system with Lamport Clocks guarantees convergence"
            .to_string(),
        svg_data: r#"<svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
            <text x="200" y="30" text-anchor="middle" font-weight="bold">Lamport Clock Ordering</text>
            <circle cx="80" cy="100" r="50" fill="#fff5e6" stroke="#ff9933" stroke-width="2"/>
            <circle cx="320" cy="100" r="50" fill="#e6f5ff" stroke="#0088cc" stroke-width="2"/>
            <text x="80" y="90" text-anchor="middle">Device A</text>
            <text x="80" y="110" text-anchor="middle" font-size="12">LC: 1,2,3</text>
            <text x="320" y="90" text-anchor="middle">Device B</text>
            <text x="320" y="110" text-anchor="middle" font-size="12">LC: 1,2,3</text>
            <path d="M 130 100 L 270 100" stroke="#22aa44" stroke-width="2" marker-end="url(#arrow)"/>
            <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><polygon points="0 0, 10 3, 0 6" fill="#22aa44"/></marker></defs>
            </svg>"#.to_string(),
    });

    // Figure 2: Message Ordering
    figures.push(PaperFigure {
        figure_id: Uuid::new_v4().to_string(),
        figure_type: "sequence".to_string(),
        title: "Figure 2: Deterministic Message Ordering".to_string(),
        caption: "Messages ordered by Lamport Clock, independent of wall-clock time"
            .to_string(),
        svg_data: r#"<svg viewBox="0 0 300 150" xmlns="http://www.w3.org/2000/svg">
            <rect x="10" y="20" width="280" height="110" fill="none" stroke="#ddd" stroke-width="1"/>
            <text x="15" y="40" font-weight="bold" font-size="12">Message Timeline</text>
            <rect x="30" y="60" width="60" height="30" fill="#e6f5ff" stroke="#0088cc" stroke-width="1" rx="3"/>
            <text x="60" y="80" text-anchor="middle" font-size="11">Msg 1</text>
            <text x="60" y="95" text-anchor="middle" font-size="10">LC=1</text>
            <rect x="120" y="60" width="60" height="30" fill="#e6f5ff" stroke="#0088cc" stroke-width="1" rx="3"/>
            <text x="150" y="80" text-anchor="middle" font-size="11">Msg 2</text>
            <text x="150" y="95" text-anchor="middle" font-size="10">LC=2</text>
            <rect x="210" y="60" width="60" height="30" fill="#e6f5ff" stroke="#0088cc" stroke-width="1" rx="3"/>
            <text x="240" y="80" text-anchor="middle" font-size="11">Msg 3</text>
            <text x="240" y="95" text-anchor="middle" font-size="10">LC=3</text>
            </svg>"#.to_string(),
    });

    (StatusCode::CREATED, Json(figures))
}
