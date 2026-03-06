use chrono::Local;
use eframe::egui;
use std::fs;
use std::io::{BufRead, BufReader, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::mpsc;
use std::time::Instant;

// ── Rhea Design System Colors ───────────────────────────────────────
const BG: egui::Color32 = egui::Color32::from_rgb(15, 15, 26);
const PANEL_BG: egui::Color32 = egui::Color32::from_rgb(26, 26, 41);
const ACCENT: egui::Color32 = egui::Color32::from_rgb(102, 217, 255);
const GREEN: egui::Color32 = egui::Color32::from_rgb(77, 230, 128);
const AMBER: egui::Color32 = egui::Color32::from_rgb(255, 199, 51);
const RED: egui::Color32 = egui::Color32::from_rgb(255, 89, 89);
const TEXT: egui::Color32 = egui::Color32::from_rgba_premultiplied(230, 230, 230, 230);
const TEXT_DIM: egui::Color32 = egui::Color32::from_rgba_premultiplied(140, 140, 160, 200);

const LOG_PATH: &str = "/tmp/0.log";
const PIDS_DIR: &str = "/Users/sa/rh.1/.pids";
const MAX_LOG_LINES: usize = 100;
const API_POLL_INTERVAL_SECS: u64 = 5;

fn api_base_url() -> String {
    std::env::var("RHEA_API_URL").unwrap_or_else(|_| "http://localhost:8000".to_string())
}

// ── API Response Types ──────────────────────────────────────────────
#[derive(Clone, serde::Deserialize, Default)]
struct ApiAgent {
    id: String,
    name: String,
    role: String,
    domain: String,
    tier: String,
    status: String,
    last_activity: Option<serde_json::Value>,
}

#[derive(Clone, serde::Deserialize)]
struct ApiStatusResponse {
    online: u32,
    busy: u32,
    offline: u32,
    total: u32,
    agents: Vec<ApiAgent>,
}

#[derive(Clone, serde::Deserialize)]
struct DelegateResponse {
    task_id: String,
    status: String,
    agent: String,
}

#[derive(Clone, serde::Deserialize)]
struct FlowTaskRef {
    agent: String,
    task_id: String,
}

#[derive(Clone, serde::Deserialize)]
struct FlowResponse {
    flow_id: String,
    mode: String,
    tasks: Vec<FlowTaskRef>,
}

enum ApiMessage {
    StatusUpdate(ApiStatusResponse),
    DelegateResult(Result<DelegateResponse, String>),
    FlowResult(Result<FlowResponse, String>),
    PollError(String),
}

// ── Agent Status ────────────────────────────────────────────────────
#[derive(Clone, Copy, PartialEq)]
enum AgentStatus {
    Running,
    Stopped,
    Busy,
}

impl AgentStatus {
    fn color(self) -> egui::Color32 {
        match self {
            AgentStatus::Running => GREEN,
            AgentStatus::Stopped => RED,
            AgentStatus::Busy => AMBER,
        }
    }

    fn label(self) -> &'static str {
        match self {
            AgentStatus::Running => "running",
            AgentStatus::Stopped => "stopped",
            AgentStatus::Busy => "busy",
        }
    }

    fn from_api(s: &str) -> Self {
        match s {
            "online" => AgentStatus::Running,
            "busy" => AgentStatus::Busy,
            _ => AgentStatus::Stopped,
        }
    }
}

// ── Selection enum ──────────────────────────────────────────────────
#[derive(Clone, PartialEq)]
enum Selection {
    Local(usize),
    Orch(usize),
}

// ── Agent Definition ────────────────────────────────────────────────
#[derive(Clone)]
struct Agent {
    name: String,
    model: String,
    status: AgentStatus,
    last_activity: String,
    log_lines: Vec<String>,
    pid: Option<u32>,
    log_path: Option<PathBuf>,
    last_log_pos: u64,
}

// ── Known agents and their detection config ─────────────────────────
struct AgentSpec {
    name: &'static str,
    model: &'static str,
    pid_file: Option<&'static str>,
    pgrep_pattern: Option<&'static str>,
    log_path: Option<&'static str>,
}

fn known_agents() -> Vec<AgentSpec> {
    vec![
        AgentSpec {
            name: "rhea-health",
            model: "daemon",
            pid_file: None,
            pgrep_pattern: Some("rhea-health"),
            log_path: Some("/tmp/rhea-health.log"),
        },
        AgentSpec {
            name: "rhea-tray",
            model: "daemon",
            pid_file: None,
            pgrep_pattern: Some("rhea-tray"),
            log_path: Some("/tmp/rhea-tray.log"),
        },
        AgentSpec {
            name: "rhea-clipboard",
            model: "daemon",
            pid_file: None,
            pgrep_pattern: Some("rhea_clipboard"),
            log_path: Some("/tmp/rhea-clipboard.log"),
        },
        AgentSpec {
            name: "rhea-session-server",
            model: "server",
            pid_file: Some("server.pid"),
            pgrep_pattern: Some("rhea-session-server"),
            log_path: Some("/tmp/rhea-session-server.log"),
        },
        AgentSpec {
            name: "rhea-angel",
            model: "game",
            pid_file: Some("angel.pid"),
            pgrep_pattern: Some("rhea-angel"),
            log_path: Some("/tmp/rhea-angel.log"),
        },
        AgentSpec {
            name: "rhea-auth",
            model: "service",
            pid_file: Some("auth.pid"),
            pgrep_pattern: Some("rhea-auth"),
            log_path: Some("/tmp/rhea-auth.log"),
        },
    ]
}

/// Check if a PID is alive via `kill -0`
fn pid_alive(pid: u32) -> bool {
    Command::new("kill")
        .args(["-0", &pid.to_string()])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

/// Try to find PID from .pids/ file
fn read_pid_file(name: &str) -> Option<u32> {
    let path = Path::new(PIDS_DIR).join(name);
    fs::read_to_string(&path)
        .ok()
        .and_then(|s| s.trim().parse().ok())
}

/// Fallback: find PID via pgrep
fn pgrep_pid(pattern: &str) -> Option<u32> {
    Command::new("pgrep")
        .args(["-f", pattern])
        .output()
        .ok()
        .and_then(|o| {
            if o.status.success() {
                String::from_utf8_lossy(&o.stdout)
                    .lines()
                    .next()
                    .and_then(|l| l.trim().parse().ok())
            } else {
                None
            }
        })
}

/// Detect agent: try PID file first, then pgrep
fn detect_agent(spec: &AgentSpec) -> Agent {
    let pid = spec
        .pid_file
        .and_then(read_pid_file)
        .filter(|&p| pid_alive(p))
        .or_else(|| spec.pgrep_pattern.and_then(pgrep_pid));

    let status = if pid.is_some() {
        AgentStatus::Running
    } else {
        AgentStatus::Stopped
    };

    let last_activity = if status == AgentStatus::Running {
        "live".to_string()
    } else {
        "offline".to_string()
    };

    let log_path = spec.log_path.map(PathBuf::from);

    Agent {
        name: spec.name.to_string(),
        model: spec.model.to_string(),
        status,
        last_activity,
        log_lines: Vec::new(),
        pid,
        log_path,
        last_log_pos: 0,
    }
}

/// Read tail lines from a log file starting at `pos`, return new position
fn read_log_tail(path: &Path, pos: u64, buf: &mut Vec<String>) -> u64 {
    let file = match fs::File::open(path) {
        Ok(f) => f,
        Err(_) => return pos,
    };
    let meta = match file.metadata() {
        Ok(m) => m,
        Err(_) => return pos,
    };
    let file_len = meta.len();
    if file_len < pos {
        // File was truncated/rotated — start over
        buf.clear();
        return read_log_tail(path, 0, buf);
    }
    if file_len == pos {
        return pos;
    }
    let mut reader = BufReader::new(file);
    if reader.seek(SeekFrom::Start(pos)).is_err() {
        return pos;
    }
    let mut new_pos = pos;
    let mut line = String::new();
    loop {
        line.clear();
        match reader.read_line(&mut line) {
            Ok(0) => break,
            Ok(n) => {
                new_pos += n as u64;
                let trimmed = line.trim_end().to_string();
                if !trimmed.is_empty() {
                    buf.push(trimmed);
                }
            }
            Err(_) => break,
        }
    }
    // Cap buffer
    if buf.len() > MAX_LOG_LINES {
        let drain = buf.len() - MAX_LOG_LINES;
        buf.drain(..drain);
    }
    new_pos
}

// ── App State ───────────────────────────────────────────────────────
struct RheaDash {
    agents: Vec<Agent>,
    selected: Option<Selection>,
    log_lines: Vec<String>,
    log_path: String,
    last_log_pos: u64,
    start_time: Instant,
    last_refresh: Instant,
    // Orchestration API
    api_base: String,
    orch_agents: Vec<ApiAgent>,
    api_rx: mpsc::Receiver<ApiMessage>,
    api_tx: mpsc::Sender<ApiMessage>,
    last_api_poll: Instant,
    api_error: Option<String>,
    api_toast: Option<(String, Instant)>,
    // Delegate dialog
    show_delegate: bool,
    delegate_target: Option<usize>,
    delegate_input: String,
    // Flow dialog
    show_flow: bool,
    flow_query: String,
    flow_mode: usize,
}

impl RheaDash {
    fn new(cc: &eframe::CreationContext<'_>) -> Self {
        let mut visuals = egui::Visuals::dark();
        visuals.panel_fill = BG;
        visuals.window_fill = PANEL_BG;
        visuals.faint_bg_color = PANEL_BG;
        visuals.extreme_bg_color = egui::Color32::from_rgb(10, 10, 18);
        visuals.widgets.noninteractive.bg_fill = PANEL_BG;
        visuals.widgets.inactive.bg_fill = PANEL_BG;
        visuals.widgets.hovered.bg_fill = egui::Color32::from_rgb(36, 36, 56);
        visuals.widgets.active.bg_fill = egui::Color32::from_rgb(46, 46, 66);
        visuals.selection.bg_fill = egui::Color32::from_rgba_premultiplied(102, 217, 255, 40);
        visuals.selection.stroke = egui::Stroke::new(1.0, ACCENT);
        visuals.override_text_color = Some(TEXT);
        cc.egui_ctx.set_visuals(visuals);

        let agents: Vec<Agent> = known_agents().iter().map(detect_agent).collect();
        let (tx, rx) = mpsc::channel();
        let api_base = api_base_url();

        // Fire initial API poll
        let url = format!("{}/orchestration/agents/status", &api_base);
        let tx_clone = tx.clone();
        std::thread::spawn(move || poll_api_status(&url, &tx_clone));

        Self {
            agents,
            selected: None,
            log_lines: Vec::new(),
            log_path: LOG_PATH.to_string(),
            last_log_pos: 0,
            start_time: Instant::now(),
            last_refresh: Instant::now(),
            api_base,
            orch_agents: Vec::new(),
            api_rx: rx,
            api_tx: tx,
            last_api_poll: Instant::now(),
            api_error: None,
            api_toast: None,
            show_delegate: false,
            delegate_target: None,
            delegate_input: String::new(),
            show_flow: false,
            flow_query: String::new(),
            flow_mode: 0,
        }
    }

    fn uptime_string(&self) -> String {
        let secs = self.start_time.elapsed().as_secs();
        let m = secs / 60;
        let s = secs % 60;
        format!("{m:02}:{s:02}")
    }

    fn running_count(&self) -> usize {
        self.agents
            .iter()
            .filter(|a| a.status != AgentStatus::Stopped)
            .count()
    }

    /// Refresh log file and agent statuses (called every ~500ms)
    fn refresh(&mut self) {
        // Read new lines from /tmp/0.log
        self.last_log_pos =
            read_log_tail(Path::new(&self.log_path), self.last_log_pos, &mut self.log_lines);

        // Refresh agent PIDs and status
        let specs = known_agents();
        for (agent, spec) in self.agents.iter_mut().zip(specs.iter()) {
            let pid = spec
                .pid_file
                .and_then(read_pid_file)
                .filter(|&p| pid_alive(p))
                .or_else(|| spec.pgrep_pattern.and_then(pgrep_pid));

            agent.pid = pid;
            agent.status = if pid.is_some() {
                AgentStatus::Running
            } else {
                AgentStatus::Stopped
            };
            agent.last_activity = if agent.status == AgentStatus::Running {
                format!("pid {}", pid.unwrap_or(0))
            } else {
                "offline".to_string()
            };
        }

        // Read per-agent logs
        for agent in &mut self.agents {
            if let Some(ref path) = agent.log_path {
                agent.last_log_pos =
                    read_log_tail(path, agent.last_log_pos, &mut agent.log_lines);
            }
        }

        // Drain API messages
        while let Ok(msg) = self.api_rx.try_recv() {
            match msg {
                ApiMessage::StatusUpdate(resp) => {
                    self.orch_agents = resp.agents;
                    self.api_error = None;
                }
                ApiMessage::DelegateResult(Ok(resp)) => {
                    self.api_toast = Some((
                        format!("✓ Delegated to {} (task {})", resp.agent, resp.task_id),
                        Instant::now(),
                    ));
                }
                ApiMessage::DelegateResult(Err(e)) => {
                    self.api_toast = Some((format!("✗ Delegate failed: {e}"), Instant::now()));
                }
                ApiMessage::FlowResult(Ok(resp)) => {
                    self.api_toast = Some((
                        format!(
                            "✓ Flow {} started ({} mode, {} agents)",
                            resp.flow_id,
                            resp.mode,
                            resp.tasks.len()
                        ),
                        Instant::now(),
                    ));
                }
                ApiMessage::FlowResult(Err(e)) => {
                    self.api_toast = Some((format!("✗ Flow failed: {e}"), Instant::now()));
                }
                ApiMessage::PollError(e) => {
                    self.api_error = Some(e);
                }
            }
        }

        // Poll API every 5 seconds
        if self.last_api_poll.elapsed().as_secs() >= API_POLL_INTERVAL_SECS {
            let url = format!("{}/orchestration/agents/status", &self.api_base);
            let tx = self.api_tx.clone();
            std::thread::spawn(move || poll_api_status(&url, &tx));
            self.last_api_poll = Instant::now();
        }

        // Expire toast after 5 seconds
        if let Some((_, t)) = &self.api_toast {
            if t.elapsed().as_secs() >= 5 {
                self.api_toast = None;
            }
        }
    }

    fn send_delegate(&self, agent_id: &str, task: &str) {
        let url = format!(
            "{}/orchestration/agents/{}/delegate",
            &self.api_base, agent_id
        );
        let body = serde_json::json!({"task": task});
        let tx = self.api_tx.clone();
        let url_owned = url;
        let body_owned = body;
        std::thread::spawn(move || {
            let result = ureq::post(&url_owned)
                .set("Content-Type", "application/json")
                .timeout(std::time::Duration::from_secs(5))
                .send_json(body_owned)
                .map_err(|e| e.to_string())
                .and_then(|resp| {
                    resp.into_json::<DelegateResponse>()
                        .map_err(|e| e.to_string())
                });
            let _ = tx.send(ApiMessage::DelegateResult(result));
        });
    }

    fn send_flow(&self, query: &str, mode: &str) {
        let url = format!("{}/orchestration/flow", &self.api_base);
        let body = serde_json::json!({"query": query, "mode": mode});
        let tx = self.api_tx.clone();
        std::thread::spawn(move || {
            let result = ureq::post(&url)
                .set("Content-Type", "application/json")
                .timeout(std::time::Duration::from_secs(5))
                .send_json(body)
                .map_err(|e| e.to_string())
                .and_then(|resp| {
                    resp.into_json::<FlowResponse>().map_err(|e| e.to_string())
                });
            let _ = tx.send(ApiMessage::FlowResult(result));
        });
    }
}

fn poll_api_status(url: &str, tx: &mpsc::Sender<ApiMessage>) {
    match ureq::get(url)
        .timeout(std::time::Duration::from_secs(3))
        .call()
    {
        Ok(resp) => match resp.into_json::<ApiStatusResponse>() {
            Ok(data) => {
                let _ = tx.send(ApiMessage::StatusUpdate(data));
            }
            Err(e) => {
                let _ = tx.send(ApiMessage::PollError(format!("parse: {e}")));
            }
        },
        Err(e) => {
            let _ = tx.send(ApiMessage::PollError(format!("connect: {e}")));
        }
    }
}

const FLOW_MODES: [&str; 3] = ["single", "dual", "consensus"];

impl eframe::App for RheaDash {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        ctx.request_repaint_after(std::time::Duration::from_millis(500));

        // Refresh data every 500ms
        if self.last_refresh.elapsed().as_millis() >= 500 {
            self.refresh();
            self.last_refresh = Instant::now();
        }

        // ── Top Panel ───────────────────────────────────────────────
        egui::TopBottomPanel::top("top_bar")
            .exact_height(28.0)
            .frame(egui::Frame::none().fill(PANEL_BG).inner_margin(egui::Margin::symmetric(12.0, 4.0)))
            .show(ctx, |ui| {
                ui.horizontal(|ui| {
                    ui.colored_label(ACCENT, egui::RichText::new("⚡ RHEA COMMAND CENTRE").strong().size(14.0));
                    ui.add_space(12.0);
                    if ui
                        .add(egui::Button::new(
                            egui::RichText::new("▶ Run Flow").size(11.0).color(TEXT),
                        ).fill(egui::Color32::from_rgb(36, 36, 56)).rounding(3.0))
                        .clicked()
                    {
                        self.show_flow = true;
                    }
                    // Toast message
                    if let Some((ref msg, _)) = self.api_toast {
                        ui.add_space(8.0);
                        let c = if msg.starts_with('✓') { GREEN } else { RED };
                        ui.colored_label(c, egui::RichText::new(msg.as_str()).size(10.0));
                    }
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        let now = Local::now().format("%H:%M:%S").to_string();
                        ui.colored_label(TEXT_DIM, egui::RichText::new(now).size(11.0));
                        ui.colored_label(TEXT_DIM, "│");
                        ui.colored_label(
                            TEXT_DIM,
                            egui::RichText::new(format!("▲ {}", self.uptime_string())).size(11.0),
                        );
                        ui.colored_label(TEXT_DIM, "│");
                        let count = self.running_count();
                        ui.colored_label(
                            GREEN,
                            egui::RichText::new(format!("{count} agents online")).size(11.0),
                        );
                        if let Some(ref err) = self.api_error {
                            ui.colored_label(TEXT_DIM, "│");
                            ui.colored_label(
                                AMBER,
                                egui::RichText::new(format!("API: {}", err)).size(9.0),
                            );
                        }
                    });
                });
            });

        // ── Bottom Panel (0.LOG LIVE) ───────────────────────────────
        egui::TopBottomPanel::bottom("dts_log")
            .exact_height(120.0)
            .frame(egui::Frame::none().fill(PANEL_BG).inner_margin(egui::Margin::symmetric(12.0, 6.0)))
            .show(ctx, |ui| {
                ui.colored_label(ACCENT, egui::RichText::new("0.LOG LIVE").strong().size(11.0));
                ui.separator();
                egui::ScrollArea::vertical()
                    .auto_shrink([false, false])
                    .stick_to_bottom(true)
                    .show(ui, |ui| {
                        if self.log_lines.is_empty() {
                            ui.colored_label(
                                TEXT_DIM,
                                egui::RichText::new(format!("Waiting for {}…", self.log_path))
                                    .monospace()
                                    .size(11.0),
                            );
                        } else {
                            for line in &self.log_lines {
                                ui.colored_label(
                                    TEXT_DIM,
                                    egui::RichText::new(line.as_str()).monospace().size(11.0),
                                );
                            }
                        }
                    });
            });

        // ── Left Panel (Agent List) ─────────────────────────────────
        egui::SidePanel::left("agents_panel")
            .exact_width(250.0)
            .frame(egui::Frame::none().fill(BG).inner_margin(egui::Margin::symmetric(8.0, 8.0)))
            .show(ctx, |ui| {
                egui::ScrollArea::vertical()
                    .auto_shrink([false, false])
                    .show(ui, |ui| {
                ui.colored_label(TEXT_DIM, egui::RichText::new("LOCAL AGENTS").strong().size(10.0));
                ui.add_space(6.0);

                let agents_snapshot: Vec<(usize, String, String, AgentStatus, String)> = self
                    .agents
                    .iter()
                    .enumerate()
                    .map(|(i, a)| {
                        (
                            i,
                            a.name.clone(),
                            a.model.clone(),
                            a.status,
                            a.last_activity.clone(),
                        )
                    })
                    .collect();

                for (idx, name, model, status, last_activity) in &agents_snapshot {
                    let is_selected = self.selected == Some(Selection::Local(*idx));
                    let card_bg = if is_selected {
                        egui::Color32::from_rgb(36, 36, 56)
                    } else {
                        PANEL_BG
                    };

                    let frame = egui::Frame::none()
                        .fill(card_bg)
                        .inner_margin(egui::Margin::symmetric(10.0, 8.0))
                        .rounding(4.0)
                        .stroke(if is_selected {
                            egui::Stroke::new(1.0, ACCENT)
                        } else {
                            egui::Stroke::NONE
                        });

                    let resp = frame.show(ui, |ui: &mut egui::Ui| {
                        ui.horizontal(|ui: &mut egui::Ui| {
                            let dot_color = status.color();
                            let (dot_rect, _) = ui.allocate_exact_size(
                                egui::vec2(8.0, 8.0),
                                egui::Sense::hover(),
                            );
                            ui.painter()
                                .circle_filled(dot_rect.center(), 4.0, dot_color);

                            ui.vertical(|ui: &mut egui::Ui| {
                                ui.label(
                                    egui::RichText::new(name.as_str())
                                        .strong()
                                        .size(13.0)
                                        .color(TEXT),
                                );
                                ui.label(
                                    egui::RichText::new(model.as_str())
                                        .size(10.0)
                                        .color(TEXT_DIM),
                                );
                                ui.horizontal(|ui: &mut egui::Ui| {
                                    ui.label(
                                        egui::RichText::new(status.label())
                                            .size(9.0)
                                            .color(status.color()),
                                    );
                                    ui.label(
                                        egui::RichText::new(format!("· {last_activity}"))
                                            .size(9.0)
                                            .color(TEXT_DIM),
                                    );
                                });
                            });
                        });
                    });

                    if resp.response.interact(egui::Sense::click()).clicked() {
                        self.selected = Some(Selection::Local(*idx));
                    }

                    ui.add_space(4.0);
                }

                // ── Orchestration Agents (A1-A8) ────────────────────
                ui.add_space(8.0);
                ui.separator();
                ui.add_space(4.0);
                ui.colored_label(TEXT_DIM, egui::RichText::new("ORCHESTRATION (A1–A8)").strong().size(10.0));
                ui.add_space(6.0);

                let orch_snapshot: Vec<(usize, String, String, String, AgentStatus, String)> = self
                    .orch_agents
                    .iter()
                    .enumerate()
                    .map(|(i, a)| {
                        let status = AgentStatus::from_api(&a.status);
                        let activity = a
                            .last_activity
                            .as_ref()
                            .map(|v| match v {
                                serde_json::Value::String(s) => s.clone(),
                                other => other.to_string(),
                            })
                            .unwrap_or_else(|| "—".to_string());
                        (i, a.id.clone(), a.name.clone(), a.role.clone(), status, activity)
                    })
                    .collect();

                if orch_snapshot.is_empty() {
                    ui.colored_label(
                        TEXT_DIM,
                        egui::RichText::new("Connecting to API…").size(10.0).italics(),
                    );
                }

                for (idx, id, name, role, status, activity) in &orch_snapshot {
                    let is_selected = self.selected == Some(Selection::Orch(*idx));
                    let card_bg = if is_selected {
                        egui::Color32::from_rgb(36, 36, 56)
                    } else {
                        PANEL_BG
                    };

                    let frame = egui::Frame::none()
                        .fill(card_bg)
                        .inner_margin(egui::Margin::symmetric(10.0, 8.0))
                        .rounding(4.0)
                        .stroke(if is_selected {
                            egui::Stroke::new(1.0, ACCENT)
                        } else {
                            egui::Stroke::NONE
                        });

                    let resp = frame.show(ui, |ui: &mut egui::Ui| {
                        ui.horizontal(|ui: &mut egui::Ui| {
                            let dot_color = status.color();
                            let (dot_rect, _) = ui.allocate_exact_size(
                                egui::vec2(8.0, 8.0),
                                egui::Sense::hover(),
                            );
                            ui.painter()
                                .circle_filled(dot_rect.center(), 4.0, dot_color);

                            ui.vertical(|ui: &mut egui::Ui| {
                                ui.label(
                                    egui::RichText::new(format!("{id} {name}"))
                                        .strong()
                                        .size(12.0)
                                        .color(TEXT),
                                );
                                ui.label(
                                    egui::RichText::new(role.as_str())
                                        .size(10.0)
                                        .color(TEXT_DIM),
                                );
                                ui.horizontal(|ui: &mut egui::Ui| {
                                    ui.label(
                                        egui::RichText::new(status.label())
                                            .size(9.0)
                                            .color(status.color()),
                                    );
                                    ui.label(
                                        egui::RichText::new(format!("· {activity}"))
                                            .size(9.0)
                                            .color(TEXT_DIM),
                                    );
                                });
                            });
                        });
                    });

                    if resp.response.interact(egui::Sense::click()).clicked() {
                        self.selected = Some(Selection::Orch(*idx));
                    }

                    ui.add_space(4.0);
                }
                    });
            });

        // ── Central Panel (Agent Output) ────────────────────────────
        egui::CentralPanel::default()
            .frame(egui::Frame::none().fill(BG).inner_margin(egui::Margin::symmetric(16.0, 12.0)))
            .show(ctx, |ui| {
                match self.selected {
                    None => {
                        ui.centered_and_justified(|ui| {
                            ui.colored_label(
                                TEXT_DIM,
                                egui::RichText::new("Select an agent to view output")
                                    .size(16.0)
                                    .italics(),
                            );
                        });
                    }
                    Some(idx) => {
                        let agent = &self.agents[idx];
                        ui.horizontal(|ui| {
                            ui.colored_label(
                                ACCENT,
                                egui::RichText::new(format!("▸ {}", agent.name))
                                    .strong()
                                    .size(14.0),
                            );
                            ui.colored_label(
                                TEXT_DIM,
                                egui::RichText::new(format!("({})", agent.model)).size(11.0),
                            );
                            let dot = agent.status.color();
                            let (r, _) = ui.allocate_exact_size(
                                egui::vec2(8.0, 8.0),
                                egui::Sense::hover(),
                            );
                            ui.painter().circle_filled(r.center(), 4.0, dot);
                            if let Some(pid) = agent.pid {
                                ui.colored_label(
                                    TEXT_DIM,
                                    egui::RichText::new(format!("PID {pid}")).size(10.0),
                                );
                            }
                        });
                        ui.separator();
                        ui.add_space(4.0);

                        egui::ScrollArea::vertical()
                            .auto_shrink([false, false])
                            .stick_to_bottom(true)
                            .show(ui, |ui| {
                                if agent.log_lines.is_empty() {
                                    let msg = match &agent.log_path {
                                        Some(p) => format!("No log file found at {}", p.display()),
                                        None => format!("No log file configured for {}", agent.name),
                                    };
                                    ui.colored_label(
                                        TEXT_DIM,
                                        egui::RichText::new(msg).monospace().size(12.0).italics(),
                                    );
                                } else {
                                    for line in &agent.log_lines {
                                        ui.colored_label(
                                            TEXT,
                                            egui::RichText::new(line.as_str())
                                                .monospace()
                                                .size(12.0),
                                        );
                                    }
                                }
                                ui.add_space(8.0);
                                ui.colored_label(
                                    TEXT_DIM,
                                    egui::RichText::new("█").monospace().size(12.0),
                                );
                            });
                    }
                }
            });
    }
}

// ── Entry Point ─────────────────────────────────────────────────────
fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([1100.0, 700.0])
            .with_min_inner_size([800.0, 500.0])
            .with_title("RHEA COMMAND CENTRE"),
        ..Default::default()
    };

    eframe::run_native(
        "RHEA COMMAND CENTRE",
        options,
        Box::new(|cc| Ok(Box::new(RheaDash::new(cc)))),
    )
}
