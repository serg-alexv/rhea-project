use chrono::Local;
use eframe::egui;
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
    name: &'static str,
    model: &'static str,
    status: AgentStatus,
    last_activity: &'static str,
    demo_log: Vec<String>,
}

fn demo_agents() -> Vec<Agent> {
    vec![
        Agent {
            name: "Rex",
            model: "Claude Opus 4",
            status: AgentStatus::Running,
            last_activity: "2s ago",
            demo_log: vec![
                "[Rex] ▸ Loaded project context from docs/state.md".into(),
                "[Rex] ▸ Scanning 14 ADRs for policy drift…".into(),
                "[Rex] ▸ rhea_bridge: 6 providers online, 31 models available".into(),
                "[Rex] ▸ Tribunal quorum: 3/3 judges ready".into(),
                "[Rex] ▸ Memory benchmark: 73/73 checks passed ✓".into(),
                "[Rex] ▸ Executing Chronos Protocol v3 cycle…".into(),
                "[Rex] ▸ Cycle complete. Next tick in 120s.".into(),
            ],
        },
        Agent {
            name: "Orion",
            model: "GPT-5.1 Codex",
            status: AgentStatus::Busy,
            last_activity: "8s ago",
            demo_log: vec![
                "[Orion] ▸ Received relay task from Rex".into(),
                "[Orion] ▸ Building rhea-dash scaffold…".into(),
                "[Orion] ▸ cargo init rhea-dash --name rhea-dash".into(),
                "[Orion] ▸ Writing Cargo.toml dependencies…".into(),
                "[Orion] ▸ Compiling eframe v0.29 with wgpu backend…".into(),
            ],
        },
        Agent {
            name: "Gemini",
            model: "Flash 2.5",
            status: AgentStatus::Running,
            last_activity: "14s ago",
            demo_log: vec![
                "[Gemini] ▸ Multimodal scan: 3 diagrams ingested".into(),
                "[Gemini] ▸ Extracted control-flow from play_frame_00.png".into(),
                "[Gemini] ▸ Cross-referencing with ontology graph…".into(),
                "[Gemini] ▸ 12 semantic links discovered.".into(),
            ],
        },
        Agent {
            name: "Hyperion",
            model: "GPT-5.4",
            status: AgentStatus::Stopped,
            last_activity: "2m ago",
            demo_log: vec![
                "[Hyperion] ▸ Last session ended: billing review".into(),
                "[Hyperion] ▸ 47 invoice line items validated".into(),
                "[Hyperion] ▸ Awaiting next dispatch from Rex.".into(),
            ],
        },
        Agent {
            name: "Sha",
            model: "Claude Haiku 4.5",
            status: AgentStatus::Running,
            last_activity: "1s ago",
            demo_log: vec![
                "[Sha] ▸ Triage queue: 0 pending, 3 resolved".into(),
                "[Sha] ▸ Voicemail inbox: empty".into(),
                "[Sha] ▸ Chat relay: heartbeat OK (ws://localhost:9090)".into(),
                "[Sha] ▸ Firestore sync: last push 4s ago".into(),
                "[Sha] ▸ Monitoring… ●".into(),
            ],
        },
    ]
}

fn demo_dts_events() -> Vec<String> {
    vec![
        "LC:0001 │ Rex      → state.md checkpoint (1847 B)".into(),
        "LC:0002 │ Sha      → triage: 3 items resolved".into(),
        "LC:0003 │ Orion    → relay ACK from Rex (task: rhea-dash)".into(),
        "LC:0004 │ Gemini   → multimodal ingest complete".into(),
        "LC:0005 │ Rex      → Chronos v3 cycle #42 started".into(),
        "LC:0006 │ Sha      → Firestore push OK (latency: 23ms)".into(),
        "LC:0007 │ Orion    → cargo build SUCCESS (rhea-dash)".into(),
        "LC:0008 │ Rex      → memory_benchmark: 73/73 ✓".into(),
        "LC:0009 │ Hyperion → session parked (idle > 120s)".into(),
        "LC:0010 │ Rex      → git push origin main (auto-commit)".into(),
    ]
}

// ── App State ───────────────────────────────────────────────────────
struct RheaDash {
    agents: Vec<Agent>,
    selected: Option<usize>,
    dts_events: Vec<String>,
    start_time: Instant,
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

        Self {
            agents: demo_agents(),
            selected: None,
            dts_events: demo_dts_events(),
            start_time: Instant::now(),
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
}

impl eframe::App for RheaDash {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        ctx.request_repaint_after(std::time::Duration::from_secs(1));

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

        // ── Bottom Panel (DTS Live) ─────────────────────────────────
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
                        for event in &self.dts_events {
                            ui.colored_label(
                                TEXT_DIM,
                                egui::RichText::new(event).monospace().size(11.0),
                            );
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
                            a.name.to_string(),
                            a.model.to_string(),
                            a.status,
                            a.last_activity.to_string(),
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
                        });
                        ui.separator();
                        ui.add_space(4.0);

                        egui::ScrollArea::vertical()
                            .auto_shrink([false, false])
                            .show(ui, |ui| {
                                for line in &agent.demo_log {
                                    ui.colored_label(
                                        TEXT,
                                        egui::RichText::new(line).monospace().size(12.0),
                                    );
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
