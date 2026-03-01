//! rhea — Rhea Command Centre TUI binary
//!
//! Three-pane terminal dashboard: agents | radio | tasks+tribunal
//! Talks to tribunal_api.py on localhost:8400.
//!
//! Usage: rhea [--api http://host:port]

use std::io;
use std::time::{Duration, Instant};

use anyhow::Result;
use crossterm::{
    event::{self, Event, KeyCode, KeyModifiers},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    prelude::*,
    widgets::{Block, Borders, Paragraph, Wrap, List, ListItem},
};
use serde::Deserialize;

// ─── API types ────────────────────────────────────────────────────────

#[derive(Debug, Deserialize, Clone)]
struct AgentStatus {
    name: String,
    alive: bool,
    pace: String,
    mode: String,
    #[serde(rename = "T_day")]
    t_day: i64,
    dollar_day: f64,
    floor_gap: i64,
    #[serde(default)]
    billing_mode: Option<String>,
    #[serde(default)]
    office_status: Option<String>,
    #[serde(default)]
    pending_msgs: Option<i64>,
    #[serde(default)]
    tasks_open: Option<i64>,
    #[serde(default)]
    budget_cap: Option<f64>,
    #[serde(default)]
    budget_remaining: Option<f64>,
    #[serde(default)]
    forecast: Option<String>,
    #[serde(default)]
    hard_fail: Option<bool>,
}

#[derive(Debug, Deserialize)]
struct AgentsResponse {
    #[serde(rename = "_ts")]
    _ts: String,
    agents: std::collections::HashMap<String, AgentStatus>,
}

#[derive(Debug, Deserialize)]
struct TaskSummary {
    total: i64,
    counts: std::collections::HashMap<String, i64>,
    active_by_priority: std::collections::HashMap<String, i64>,
    #[serde(default)]
    stale_count: Option<i64>,
}

#[derive(Debug, Deserialize, Clone)]
struct FeedItem {
    #[serde(default)]
    ts: String,
    #[serde(default)]
    sender: String,
    #[serde(default)]
    text: String,
    #[serde(default)]
    r#type: String,
}

#[derive(Debug, Deserialize)]
struct FeedResponse {
    items: Vec<FeedItem>,
    total: i64,
}

// ─── App state ────────────────────────────────────────────────────────

struct AppState {
    api_base: String,
    agents: Vec<AgentStatus>,
    tasks: Option<TaskSummary>,
    radio: Vec<FeedItem>,
    status_msg: String,
    tribunal_input: String,
    tribunal_result: String,
    focus: Focus,
    running: bool,
    last_poll: Instant,
}

#[derive(PartialEq)]
enum Focus {
    Dashboard,
    Tribunal,
}

impl AppState {
    fn new(api_base: String) -> Self {
        Self {
            api_base,
            agents: vec![],
            tasks: None,
            radio: vec![],
            status_msg: "starting...".into(),
            tribunal_input: String::new(),
            tribunal_result: String::new(),
            focus: Focus::Dashboard,
            running: true,
            last_poll: Instant::now() - Duration::from_secs(60),
        }
    }
}

// ─── API calls ────────────────────────────────────────────────────────

async fn fetch_agents(api: &str) -> Result<Vec<AgentStatus>> {
    let resp: AgentsResponse = reqwest::Client::new()
        .get(format!("{api}/agents/status"))
        .header("X-API-Key", "dev-bypass")
        .timeout(Duration::from_secs(5))
        .send()
        .await?
        .json()
        .await?;
    let mut agents: Vec<AgentStatus> = resp.agents.into_values().collect();
    agents.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(agents)
}

async fn fetch_tasks(api: &str) -> Result<TaskSummary> {
    let resp: TaskSummary = reqwest::Client::new()
        .get(format!("{api}/tasks/summary"))
        .header("X-API-Key", "dev-bypass")
        .timeout(Duration::from_secs(5))
        .send()
        .await?
        .json()
        .await?;
    Ok(resp)
}

async fn fetch_radio(api: &str) -> Result<Vec<FeedItem>> {
    let resp: FeedResponse = reqwest::Client::new()
        .get(format!("{api}/feed"))
        .header("X-API-Key", "dev-bypass")
        .timeout(Duration::from_secs(5))
        .send()
        .await?
        .json()
        .await?;
    Ok(resp.items)
}

async fn wake_agent(api: &str, agent: &str) -> Result<()> {
    reqwest::Client::new()
        .post(format!("{api}/agents/wake/{agent}"))
        .header("X-API-Key", "dev-bypass")
        .timeout(Duration::from_secs(5))
        .send()
        .await?;
    Ok(())
}

async fn submit_tribunal(api: &str, claim: &str) -> Result<String> {
    let body = serde_json::json!({"prompt": claim, "mode": "tribunal"});
    let resp: serde_json::Value = reqwest::Client::new()
        .post(format!("{api}/tribunal"))
        .header("X-API-Key", "dev-bypass")
        .header("Content-Type", "application/json")
        .timeout(Duration::from_secs(30))
        .json(&body)
        .send()
        .await?
        .json()
        .await?;
    let agreement = resp["agreement_score"].as_f64().unwrap_or(0.0);
    let confidence = resp["confidence"].as_f64().unwrap_or(0.0);
    let verdict = resp["response"].as_str().unwrap_or("no response");
    let models = resp["models_used"]
        .as_array()
        .map(|a| {
            a.iter()
                .filter_map(|v| v.as_str())
                .collect::<Vec<_>>()
                .join(", ")
        })
        .unwrap_or_default();
    Ok(format!(
        "Agreement: {:.0}% | Confidence: {:.0}%\nModels: {}\n\n{}",
        agreement * 100.0,
        confidence * 100.0,
        models,
        &verdict[..verdict.len().min(300)]
    ))
}

// ─── UI rendering ─────────────────────────────────────────────────────

fn draw(frame: &mut Frame, state: &AppState) {
    let outer = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(1), Constraint::Length(1)])
        .split(frame.area());

    let main_area = outer[0];
    let status_area = outer[1];

    // Three columns: agents | radio | right (tasks + tribunal)
    let cols = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(25),
            Constraint::Percentage(45),
            Constraint::Percentage(30),
        ])
        .split(main_area);

    draw_agents(frame, cols[0], state);
    draw_radio(frame, cols[1], state);

    // Right column: tasks top, tribunal bottom
    let right = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(40), Constraint::Percentage(60)])
        .split(cols[2]);
    draw_tasks(frame, right[0], state);
    draw_tribunal(frame, right[1], state);

    // Status bar
    let status = Paragraph::new(Line::from(vec![
        Span::styled(" q", Style::default().fg(Color::Yellow).bold()),
        Span::raw(":quit "),
        Span::styled("r", Style::default().fg(Color::Yellow).bold()),
        Span::raw(":refresh "),
        Span::styled("w", Style::default().fg(Color::Yellow).bold()),
        Span::raw(":wake "),
        Span::styled("t", Style::default().fg(Color::Yellow).bold()),
        Span::raw(":tribunal "),
        Span::styled("Esc", Style::default().fg(Color::Yellow).bold()),
        Span::raw(":back  "),
        Span::styled(&state.status_msg, Style::default().fg(Color::DarkGray)),
    ]))
    .style(Style::default().bg(Color::Rgb(20, 20, 30)));
    frame.render_widget(status, status_area);
}

fn draw_agents(frame: &mut Frame, area: Rect, state: &AppState) {
    let block = Block::default()
        .title(" AGENTS ")
        .title_style(Style::default().fg(Color::Cyan).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Rgb(40, 40, 60)));

    if state.agents.is_empty() {
        let p = Paragraph::new("No data").style(Style::default().fg(Color::DarkGray)).block(block);
        frame.render_widget(p, area);
        return;
    }

    let mut items = vec![];
    let mut total_tok: i64 = 0;
    let mut total_cost: f64 = 0.0;
    let mut alive = 0;

    for a in &state.agents {
        let dot_color = match a.pace.as_str() {
            "green" => Color::Green,
            "yellow" => Color::Yellow,
            _ => Color::Red,
        };
        let dot = if a.alive { "●" } else { "○" };
        let mode_color = match a.mode.as_str() {
            "normal" => Color::Green,
            "cooldown" => Color::Yellow,
            _ => Color::Red,
        };
        let tok = a.t_day;
        total_tok += tok;
        total_cost += a.dollar_day;
        if a.alive {
            alive += 1;
        }
        let tok_str = if tok >= 1_000_000 {
            format!("{}M", tok / 1_000_000)
        } else if tok >= 1_000 {
            format!("{}K", tok / 1_000)
        } else {
            format!("{}", tok)
        };
        let pending = a.pending_msgs.unwrap_or(0);
        let pend_str = if pending > 0 {
            format!(" [{}msg]", pending)
        } else {
            String::new()
        };

        let line = Line::from(vec![
            Span::styled(format!("{dot} "), Style::default().fg(dot_color)),
            Span::styled(format!("{:<8}", a.name), Style::default().fg(Color::White).bold()),
            Span::styled(format!(" {:<9}", a.mode), Style::default().fg(mode_color)),
            Span::styled(format!(" {:>6}", tok_str), Style::default().fg(Color::Cyan)),
            Span::styled(format!(" ${:.2}", a.dollar_day), Style::default().fg(Color::Yellow)),
            Span::styled(pend_str, Style::default().fg(Color::Yellow)),
        ]);
        items.push(ListItem::new(line));

        // Budget gauge if applicable
        if let Some(cap) = a.budget_cap {
            if cap > 0.0 {
                let used = if let Some(rem) = a.budget_remaining {
                    ((cap - rem) / cap).clamp(0.0, 1.0)
                } else {
                    (a.dollar_day / cap).clamp(0.0, 1.0)
                };
                let gauge_color = if used < 0.6 {
                    Color::Green
                } else if used < 0.85 {
                    Color::Yellow
                } else {
                    Color::Red
                };
                let rem_str = a
                    .budget_remaining
                    .map(|r| format!("${:.2} left", r))
                    .unwrap_or_default();
                let gauge_line = Line::from(vec![
                    Span::raw("  "),
                    Span::styled(
                        "▓".repeat((used * 16.0) as usize),
                        Style::default().fg(gauge_color),
                    ),
                    Span::styled(
                        "░".repeat(16 - (used * 16.0) as usize),
                        Style::default().fg(Color::Rgb(40, 40, 50)),
                    ),
                    Span::styled(format!(" {rem_str}"), Style::default().fg(Color::DarkGray)),
                ]);
                items.push(ListItem::new(gauge_line));
            }
        }
    }

    // Summary line
    let total_str = if total_tok >= 1_000_000 {
        format!("{}M", total_tok / 1_000_000)
    } else if total_tok >= 1_000 {
        format!("{}K", total_tok / 1_000)
    } else {
        format!("{}", total_tok)
    };
    items.push(ListItem::new(Line::from("")));
    items.push(ListItem::new(Line::from(vec![
        Span::styled(
            format!(
                " Σ {} tok ${:.2} | {}/{} alive",
                total_str,
                total_cost,
                alive,
                state.agents.len()
            ),
            Style::default().fg(Color::White).bold(),
        ),
    ])));

    let list = List::new(items).block(block);
    frame.render_widget(list, area);
}

fn draw_radio(frame: &mut Frame, area: Rect, state: &AppState) {
    let block = Block::default()
        .title(" RADIO ")
        .title_style(Style::default().fg(Color::Cyan).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Rgb(40, 40, 60)));

    if state.radio.is_empty() {
        let p = Paragraph::new("No radio events")
            .style(Style::default().fg(Color::DarkGray))
            .block(block);
        frame.render_widget(p, area);
        return;
    }

    let inner_height = area.height.saturating_sub(2) as usize;
    let start = state.radio.len().saturating_sub(inner_height);
    let visible = &state.radio[start..];

    let items: Vec<ListItem> = visible
        .iter()
        .map(|item| {
            let ts = if item.ts.len() >= 19 {
                &item.ts[11..19]
            } else {
                "        "
            };
            let sender = item.sender.to_uppercase();
            let sender_color = match sender.as_str() {
                "REX" => Color::Cyan,
                "ORION" => Color::Magenta,
                "GEMINI" => Color::Yellow,
                "HUMAN" => Color::Green,
                "RELAY" => Color::Rgb(255, 165, 0),
                _ => Color::Gray,
            };
            let text = item.text.replace('\n', " ");
            let text = if text.len() > 100 {
                format!("{}…", &text[..100])
            } else {
                text
            };
            ListItem::new(Line::from(vec![
                Span::styled(format!("{ts} "), Style::default().fg(Color::DarkGray)),
                Span::styled(
                    format!("{:<6}", &sender[..sender.len().min(6)]),
                    Style::default().fg(sender_color).bold(),
                ),
                Span::styled(format!(" {text}"), Style::default().fg(Color::Rgb(180, 180, 200))),
            ]))
        })
        .collect();

    let list = List::new(items).block(block);
    frame.render_widget(list, area);
}

fn draw_tasks(frame: &mut Frame, area: Rect, state: &AppState) {
    let block = Block::default()
        .title(" TASKS ")
        .title_style(Style::default().fg(Color::Cyan).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Rgb(40, 40, 60)));

    let text = if let Some(ref t) = state.tasks {
        let counts = &t.counts;
        let mut lines = vec![
            Line::from(vec![
                Span::styled("Total:   ", Style::default().fg(Color::DarkGray)),
                Span::styled(format!("{}", t.total), Style::default().fg(Color::White)),
            ]),
            Line::from(vec![
                Span::styled("Open:    ", Style::default().fg(Color::DarkGray)),
                Span::styled(
                    format!("{}", counts.get("open").unwrap_or(&0)),
                    Style::default().fg(Color::Green),
                ),
            ]),
            Line::from(vec![
                Span::styled("Claimed: ", Style::default().fg(Color::DarkGray)),
                Span::styled(
                    format!("{}", counts.get("claimed").unwrap_or(&0)),
                    Style::default().fg(Color::Cyan),
                ),
            ]),
            Line::from(vec![
                Span::styled("Done:    ", Style::default().fg(Color::DarkGray)),
                Span::styled(
                    format!("{}", counts.get("done").unwrap_or(&0)),
                    Style::default().fg(Color::DarkGray),
                ),
            ]),
        ];
        if !t.active_by_priority.is_empty() {
            let parts: String = t
                .active_by_priority
                .iter()
                .map(|(k, v)| format!("{k}={v}"))
                .collect::<Vec<_>>()
                .join(" ");
            lines.push(Line::from(Span::styled(
                format!("Priority: {parts}"),
                Style::default().fg(Color::Yellow),
            )));
        }
        let stale = t.stale_count.unwrap_or(0);
        if stale > 0 {
            lines.push(Line::from(Span::styled(
                format!("⚠ {stale} stale"),
                Style::default().fg(Color::Red).bold(),
            )));
        }
        Text::from(lines)
    } else {
        Text::styled("No data", Style::default().fg(Color::DarkGray))
    };

    let p = Paragraph::new(text).block(block);
    frame.render_widget(p, area);
}

fn draw_tribunal(frame: &mut Frame, area: Rect, state: &AppState) {
    let border_color = if state.focus == Focus::Tribunal {
        Color::Cyan
    } else {
        Color::Rgb(40, 40, 60)
    };
    let block = Block::default()
        .title(" TRIBUNAL ")
        .title_style(Style::default().fg(Color::Cyan).bold())
        .borders(Borders::ALL)
        .border_style(Style::default().fg(border_color));

    let inner = block.inner(area);
    frame.render_widget(block, area);

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(3), Constraint::Min(1)])
        .split(inner);

    // Input line
    let input_block = Block::default()
        .borders(Borders::ALL)
        .border_style(Style::default().fg(if state.focus == Focus::Tribunal {
            Color::Yellow
        } else {
            Color::Rgb(40, 40, 50)
        }));
    let input_text = if state.tribunal_input.is_empty() && state.focus != Focus::Tribunal {
        Paragraph::new(Span::styled(
            "Press t to enter claim...",
            Style::default().fg(Color::DarkGray),
        ))
    } else {
        Paragraph::new(Span::styled(
            &state.tribunal_input,
            Style::default().fg(Color::White),
        ))
    };
    frame.render_widget(input_text.block(input_block), chunks[0]);

    // Result
    let result = Paragraph::new(state.tribunal_result.as_str())
        .style(Style::default().fg(Color::Rgb(180, 180, 200)))
        .wrap(Wrap { trim: true });
    frame.render_widget(result, chunks[1]);
}

// ─── Main loop ────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    let api = std::env::var("RHEA_API").unwrap_or_else(|_| "http://localhost:8400".into());

    // Terminal setup
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut state = AppState::new(api);
    let poll_interval = Duration::from_secs(5);

    while state.running {
        // Poll data every 5s
        if state.last_poll.elapsed() >= poll_interval {
            state.last_poll = Instant::now();
            let api = state.api_base.clone();
            match fetch_agents(&api).await {
                Ok(a) => state.agents = a,
                Err(e) => state.status_msg = format!("agents: {e}"),
            }
            match fetch_tasks(&api).await {
                Ok(t) => state.tasks = Some(t),
                Err(e) => state.status_msg = format!("tasks: {e}"),
            }
            match fetch_radio(&api).await {
                Ok(r) => state.radio = r,
                Err(e) => state.status_msg = format!("radio: {e}"),
            }
            let alive = state.agents.iter().filter(|a| a.alive).count();
            let total = state.agents.len();
            let now = {
                let d = std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs();
                let secs = (d % 86400) as u32;
                let h = secs / 3600;
                let m = (secs % 3600) / 60;
                let s = secs % 60;
                format!("{h:02}:{m:02}:{s:02}")
            };
            state.status_msg = format!("{now} | {alive}/{total} alive | poll ok");
        }

        terminal.draw(|frame| draw(frame, &state))?;

        // Non-blocking event poll (100ms tick)
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                match state.focus {
                    Focus::Dashboard => match key.code {
                        KeyCode::Char('q') => state.running = false,
                        KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                            state.running = false
                        }
                        KeyCode::Char('r') => {
                            state.last_poll = Instant::now() - Duration::from_secs(60);
                            state.status_msg = "refreshing...".into();
                        }
                        KeyCode::Char('w') => {
                            let api = state.api_base.clone();
                            for agent in ["REX", "ORION", "GEMINI", "HYPERION"] {
                                let _ = wake_agent(&api, agent).await;
                            }
                            state.status_msg = "wake sent to all agents".into();
                        }
                        KeyCode::Char('t') => {
                            state.focus = Focus::Tribunal;
                        }
                        _ => {}
                    },
                    Focus::Tribunal => match key.code {
                        KeyCode::Esc => {
                            state.focus = Focus::Dashboard;
                        }
                        KeyCode::Enter => {
                            if !state.tribunal_input.trim().is_empty() {
                                let claim = state.tribunal_input.clone();
                                state.tribunal_input.clear();
                                state.tribunal_result = "Evaluating...".into();
                                state.focus = Focus::Dashboard;
                                let api = state.api_base.clone();
                                match submit_tribunal(&api, &claim).await {
                                    Ok(r) => state.tribunal_result = r,
                                    Err(e) => {
                                        state.tribunal_result = format!("Error: {e}")
                                    }
                                }
                            }
                        }
                        KeyCode::Backspace => {
                            state.tribunal_input.pop();
                        }
                        KeyCode::Char(c) => {
                            state.tribunal_input.push(c);
                        }
                        _ => {}
                    },
                }
            }
        }
    }

    // Cleanup
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    Ok(())
}
