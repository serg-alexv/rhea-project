use chrono::Local;
use eframe::egui;
use std::fs;
use std::io::{BufRead, BufReader, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use std::process::Command;
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
    selected: Option<usize>,
    log_lines: Vec<String>,
    log_path: String,
    last_log_pos: u64,
    start_time: Instant,
    last_refresh: Instant,
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

        Self {
            agents,
            selected: None,
            log_lines: Vec::new(),
            log_path: LOG_PATH.to_string(),
            last_log_pos: 0,
            start_time: Instant::now(),
            last_refresh: Instant::now(),
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
    }
}

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
                ui.colored_label(TEXT_DIM, egui::RichText::new("AGENTS").strong().size(10.0));
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
                    let is_selected = self.selected == Some(*idx);
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
                        self.selected = Some(*idx);
                    }

                    ui.add_space(4.0);
                }
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
