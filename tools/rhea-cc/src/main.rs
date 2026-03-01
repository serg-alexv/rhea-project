//! rhea — Rhea Command Centre TUI binary
//!
//! Three-pane terminal dashboard with full controls.
//! Talks to tribunal_api.py on localhost:8400.
//!
//! Usage: rhea
//!        RHEA_API=http://host:port rhea

use std::io;
use std::time::{Duration, Instant};

use anyhow::Result;
use crossterm::{
    event::{self, Event, KeyCode, KeyEvent, KeyModifiers},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    prelude::*,
    widgets::{Block, Borders, Paragraph, Wrap, List, ListItem, Scrollbar, ScrollbarOrientation, ScrollbarState},
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
    tasks_claimed: Option<i64>,
    #[serde(default)]
    budget_cap: Option<f64>,
    #[serde(default)]
    budget_remaining: Option<f64>,
    #[serde(default)]
    forecast: Option<String>,
    #[serde(default)]
    hard_fail: Option<bool>,
    #[serde(default)]
    lease_expired: Option<bool>,
    #[serde(default)]
    last_activity: Option<String>,
}

#[derive(Debug, Deserialize)]
struct AgentsResponse {
    #[serde(rename = "_ts")]
    _ts: String,
    agents: std::collections::HashMap<String, AgentStatus>,
}

#[derive(Debug, Deserialize, Clone)]
struct TaskSummary {
    total: i64,
    counts: std::collections::HashMap<String, i64>,
    active_by_priority: std::collections::HashMap<String, i64>,
    #[serde(default)]
    stale_count: Option<i64>,
    #[serde(default)]
    claimed_by_agent: Option<std::collections::HashMap<String, i64>>,
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
    #[serde(default)]
    receiver: Option<String>,
}

#[derive(Debug, Deserialize)]
struct FeedResponse {
    items: Vec<FeedItem>,
    #[allow(dead_code)]
    total: i64,
}

#[derive(Debug, Deserialize, Clone)]
struct TaskItem {
    #[serde(default)]
    id: Option<String>,
    #[serde(default)]
    title: String,
    #[serde(default)]
    status: String,
    #[serde(default)]
    priority: String,
    #[serde(default)]
    agent: String,
}

#[derive(Debug, Deserialize)]
struct TaskListResponse {
    tasks: Vec<TaskItem>,
}

// ─── App state ────────────────────────────────────────────────────────

#[derive(PartialEq, Clone, Copy)]
enum Panel {
    Agents,
    Radio,
    Tasks,
    Tribunal,
}

#[derive(PartialEq)]
enum InputMode {
    Normal,
    TribunalInput,
    RadioCompose,
    TaskCreate,
}

struct AppState {
    api_base: String,
    agents: Vec<AgentStatus>,
    tasks: Option<TaskSummary>,
    task_list: Vec<TaskItem>,
    radio: Vec<FeedItem>,
    status_msg: String,

    // Tribunal
    tribunal_input: String,
    tribunal_result: String,

    // Radio composer
    radio_input: String,

    // Task creator
    task_input: String,

    // Navigation
    active_panel: Panel,
    input_mode: InputMode,
    agent_cursor: usize,
    radio_scroll: usize,
    task_scroll: usize,

    running: bool,
    last_poll: Instant,
    show_task_list: bool,
}

const PANELS: [Panel; 4] = [Panel::Agents, Panel::Radio, Panel::Tasks, Panel::Tribunal];

impl AppState {
    fn new(api_base: String) -> Self {
        Self {
            api_base,
            agents: vec![],
            tasks: None,
            task_list: vec![],
            radio: vec![],
            status_msg: "starting...".into(),
            tribunal_input: String::new(),
            tribunal_result: String::new(),
            radio_input: String::new(),
            task_input: String::new(),
            active_panel: Panel::Agents,
            input_mode: InputMode::Normal,
            agent_cursor: 0,
            radio_scroll: 0,
            task_scroll: 0,
            running: true,
            last_poll: Instant::now() - Duration::from_secs(60),
            show_task_list: false,
        }
    }

    fn selected_agent(&self) -> Option<&AgentStatus> {
        self.agents.get(self.agent_cursor)
    }
}

// ─── API calls ────────────────────────────────────────────────────────

fn client() -> reqwest::Client {
    reqwest::Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
        .unwrap()
}

async fn fetch_agents(api: &str) -> Result<Vec<AgentStatus>> {
    let resp: AgentsResponse = client()
        .get(format!("{api}/agents/status"))
        .header("X-API-Key", "dev-bypass")
        .send().await?.json().await?;
    let mut agents: Vec<AgentStatus> = resp.agents.into_values().collect();
    agents.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(agents)
}

async fn fetch_tasks(api: &str) -> Result<TaskSummary> {
    Ok(client().get(format!("{api}/tasks/summary"))
        .header("X-API-Key", "dev-bypass")
        .send().await?.json().await?)
}

async fn fetch_task_list(api: &str) -> Result<Vec<TaskItem>> {
    let resp: TaskListResponse = client()
        .get(format!("{api}/tasks"))
        .header("X-API-Key", "dev-bypass")
        .send().await?.json().await?;
    Ok(resp.tasks)
}

async fn fetch_radio(api: &str) -> Result<Vec<FeedItem>> {
    let resp: FeedResponse = client()
        .get(format!("{api}/feed"))
        .header("X-API-Key", "dev-bypass")
        .send().await?.json().await?;
    Ok(resp.items)
}

async fn wake_agent(api: &str, agent: &str) -> Result<()> {
    client().post(format!("{api}/agents/wake/{agent}"))
        .header("X-API-Key", "dev-bypass")
        .send().await?;
    Ok(())
}

async fn ping_agent(api: &str, agent: &str) -> Result<()> {
    let body = serde_json::json!({
        "sender": "human",
        "text": format!("PING {agent}"),
        "type": "radio"
    });
    client().post(format!("{api}/feed/push"))
        .header("X-API-Key", "dev-bypass")
        .json(&body)
        .send().await?;
    Ok(())
}

async fn send_radio(api: &str, text: &str) -> Result<()> {
    let body = serde_json::json!({
        "sender": "human",
        "receiver": "all",
        "type": "radio",
        "text": text
    });
    client().post(format!("{api}/feed/push"))
        .header("X-API-Key", "dev-bypass")
        .json(&body)
        .send().await?;
    Ok(())
}

async fn create_task(api: &str, title: &str) -> Result<()> {
    let url = format!("{api}/tasks?title={}&priority=P1&agent=rex",
        urlencoding::encode(title));
    client().post(&url)
        .header("X-API-Key", "dev-bypass")
        .send().await?;
    Ok(())
}

async fn submit_tribunal(api: &str, claim: &str) -> Result<String> {
    let body = serde_json::json!({"prompt": claim, "mode": "tribunal"});
    let resp: serde_json::Value = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .build()?
        .post(format!("{api}/tribunal"))
        .header("X-API-Key", "dev-bypass")
        .json(&body)
        .send().await?.json().await?;
    let agreement = resp["agreement_score"].as_f64().unwrap_or(0.0);
    let confidence = resp["confidence"].as_f64().unwrap_or(0.0);
    let verdict = resp["response"].as_str().unwrap_or("no response");
    let models = resp["models_used"]
        .as_array()
        .map(|a| a.iter().filter_map(|v| v.as_str()).collect::<Vec<_>>().join(", "))
        .unwrap_or_default();
    Ok(format!(
        "Agreement: {:.0}% | Confidence: {:.0}%\nModels: {}\n\n{}",
        agreement * 100.0, confidence * 100.0, models,
        &verdict[..verdict.len().min(500)]
    ))
}

// ─── Rendering ────────────────────────────────────────────────────────

fn now_hms() -> String {
    let d = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs();
    let s = (d % 86400) as u32;
    format!("{:02}:{:02}:{:02}", s / 3600, (s % 3600) / 60, s % 60)
}

fn format_tokens(n: i64) -> String {
    if n >= 1_000_000 { format!("{}M", n / 1_000_000) }
    else if n >= 1_000 { format!("{}K", n / 1_000) }
    else { format!("{n}") }
}

fn panel_border(active: Panel, this: Panel) -> Style {
    if active == this {
        Style::default().fg(Color::Cyan)
    } else {
        Style::default().fg(Color::Rgb(40, 40, 60))
    }
}

fn draw(frame: &mut Frame, state: &AppState) {
    let outer = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(1), Constraint::Length(1)])
        .split(frame.area());

    let main_area = outer[0];
    let status_area = outer[1];

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

    let right = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Percentage(40), Constraint::Percentage(60)])
        .split(cols[2]);

    if state.show_task_list {
        draw_task_list(frame, right[0], state);
    } else {
        draw_tasks(frame, right[0], state);
    }
    draw_tribunal(frame, right[1], state);

    // Status bar with context-sensitive help
    let help = match state.input_mode {
        InputMode::Normal => match state.active_panel {
            Panel::Agents => "↑↓:select  Enter:wake  p:ping  w:wake-all  Tab:next  t:tribunal  m:radio  n:task  l:list  q:quit",
            Panel::Radio => "↑↓:scroll  m:compose  Tab:next  q:quit",
            Panel::Tasks => "↑↓:scroll  n:new-task  l:toggle-list  Tab:next  q:quit",
            Panel::Tribunal => "t:input  Tab:next  q:quit",
        },
        InputMode::TribunalInput => "Enter:submit  Esc:cancel",
        InputMode::RadioCompose => "Enter:send  Esc:cancel",
        InputMode::TaskCreate => "Enter:create  Esc:cancel",
    };

    let status = Paragraph::new(Line::from(vec![
        Span::styled(format!(" {} ", now_hms()), Style::default().fg(Color::DarkGray)),
        Span::styled(help, Style::default().fg(Color::Rgb(100, 100, 130))),
        Span::styled(format!("  {}", state.status_msg), Style::default().fg(Color::DarkGray)),
    ]))
    .style(Style::default().bg(Color::Rgb(15, 15, 25)));
    frame.render_widget(status, status_area);
}

fn draw_agents(frame: &mut Frame, area: Rect, state: &AppState) {
    let title = format!(" AGENTS ({}) ", state.agents.len());
    let block = Block::default()
        .title(title)
        .title_style(Style::default().fg(Color::Cyan).bold())
        .borders(Borders::ALL)
        .border_style(panel_border(state.active_panel, Panel::Agents));

    if state.agents.is_empty() {
        frame.render_widget(
            Paragraph::new("No data").style(Style::default().fg(Color::DarkGray)).block(block),
            area,
        );
        return;
    }

    let mut items = vec![];
    let mut total_tok: i64 = 0;
    let mut total_cost: f64 = 0.0;
    let mut alive = 0;

    for (i, a) in state.agents.iter().enumerate() {
        let is_selected = state.active_panel == Panel::Agents && i == state.agent_cursor;
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
        total_tok += a.t_day;
        total_cost += a.dollar_day;
        if a.alive { alive += 1; }

        let tok_str = format_tokens(a.t_day);
        let pending = a.pending_msgs.unwrap_or(0);
        let pend_str = if pending > 0 { format!(" [{pending}✉]") } else { String::new() };
        let tasks = a.tasks_open.unwrap_or(0);
        let task_str = if tasks > 0 { format!(" {tasks}T") } else { String::new() };

        let cursor = if is_selected { "▸" } else { " " };

        let line = Line::from(vec![
            Span::styled(cursor, Style::default().fg(Color::Cyan)),
            Span::styled(format!("{dot} "), Style::default().fg(dot_color)),
            Span::styled(format!("{:<8}", a.name), Style::default().fg(Color::White).bold()),
            Span::styled(format!(" {:<8}", a.mode), Style::default().fg(mode_color)),
            Span::styled(format!(" {:>5}", tok_str), Style::default().fg(Color::Cyan)),
            Span::styled(format!(" ${:.2}", a.dollar_day), Style::default().fg(Color::Yellow)),
            Span::styled(pend_str, Style::default().fg(Color::Yellow)),
            Span::styled(task_str, Style::default().fg(Color::Rgb(100, 100, 140))),
        ]);
        let style = if is_selected {
            Style::default().bg(Color::Rgb(30, 30, 50))
        } else {
            Style::default()
        };
        items.push(ListItem::new(line).style(style));

        // Budget bar
        if let Some(cap) = a.budget_cap {
            if cap > 0.0 {
                let used = a.budget_remaining
                    .map(|rem| ((cap - rem) / cap).clamp(0.0, 1.0))
                    .unwrap_or_else(|| (a.dollar_day / cap).clamp(0.0, 1.0));
                let gc = if used < 0.6 { Color::Green } else if used < 0.85 { Color::Yellow } else { Color::Red };
                let filled = (used * 14.0) as usize;
                let empty = 14 - filled;
                let rem_str = a.budget_remaining.map(|r| format!("${r:.1}")).unwrap_or_default();
                items.push(ListItem::new(Line::from(vec![
                    Span::raw("  "),
                    Span::styled("▓".repeat(filled), Style::default().fg(gc)),
                    Span::styled("░".repeat(empty), Style::default().fg(Color::Rgb(30, 30, 45))),
                    Span::styled(format!(" {rem_str}"), Style::default().fg(Color::DarkGray)),
                ])));
            }
        }
    }

    // Separator + summary
    items.push(ListItem::new(Line::from(
        Span::styled("─".repeat(30), Style::default().fg(Color::Rgb(40, 40, 60)))
    )));
    items.push(ListItem::new(Line::from(vec![
        Span::styled(
            format!(" Σ {} tok ${:.2} | {}/{} alive",
                format_tokens(total_tok), total_cost, alive, state.agents.len()),
            Style::default().fg(Color::White).bold(),
        ),
    ])));

    let list = List::new(items).block(block);
    frame.render_widget(list, area);
}

fn draw_radio(frame: &mut Frame, area: Rect, state: &AppState) {
    let title = format!(" RADIO ({}) ", state.radio.len());
    let block = Block::default()
        .title(title)
        .title_style(Style::default().fg(Color::Cyan).bold())
        .borders(Borders::ALL)
        .border_style(panel_border(state.active_panel, Panel::Radio));

    let inner = block.inner(area);
    let inner_height = inner.height as usize;

    // If in compose mode, reserve bottom 3 lines for input
    let (list_area, compose_area) = if state.input_mode == InputMode::RadioCompose {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([Constraint::Min(1), Constraint::Length(3)])
            .split(inner);
        (chunks[0], Some(chunks[1]))
    } else {
        (inner, None)
    };

    frame.render_widget(block, area);

    if state.radio.is_empty() {
        frame.render_widget(
            Paragraph::new("No radio events").style(Style::default().fg(Color::DarkGray)),
            list_area,
        );
    } else {
        let avail = list_area.height as usize;
        let scroll = state.radio_scroll.min(state.radio.len().saturating_sub(avail));
        let start = state.radio.len().saturating_sub(avail + scroll);
        let end = state.radio.len().saturating_sub(scroll);
        let visible = &state.radio[start..end];

        let items: Vec<ListItem> = visible.iter().map(|item| {
            let ts = if item.ts.len() >= 19 { &item.ts[11..19] } else { "        " };
            let sender = item.sender.to_uppercase();
            let sc = match sender.as_str() {
                "REX" => Color::Cyan,
                "ORION" => Color::Magenta,
                "GEMINI" => Color::Yellow,
                "HUMAN" => Color::Green,
                "RELAY" => Color::Rgb(255, 165, 0),
                "TRIBUNAL" | "TRIBUN" => Color::Rgb(0, 200, 200),
                _ => Color::Gray,
            };
            let text = item.text.replace('\n', " ");
            let text = if text.len() > 120 { format!("{}…", &text[..120]) } else { text };
            let recv = item.receiver.as_deref().unwrap_or("");
            let arrow = if !recv.is_empty() && recv != "all" {
                format!("→{} ", recv.to_uppercase())
            } else {
                String::new()
            };
            ListItem::new(Line::from(vec![
                Span::styled(format!("{ts} "), Style::default().fg(Color::DarkGray)),
                Span::styled(format!("{:<6}", &sender[..sender.len().min(6)]), Style::default().fg(sc).bold()),
                Span::styled(arrow, Style::default().fg(sc).dim()),
                Span::styled(text, Style::default().fg(Color::Rgb(180, 180, 200))),
            ]))
        }).collect();

        frame.render_widget(List::new(items), list_area);
    }

    // Radio compose box
    if let Some(ca) = compose_area {
        let input_block = Block::default()
            .title(" Broadcast ")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Yellow));
        let cursor = if state.radio_input.is_empty() { "type message..." } else { &state.radio_input };
        let p = Paragraph::new(Span::styled(cursor, Style::default().fg(
            if state.radio_input.is_empty() { Color::DarkGray } else { Color::White }
        ))).block(input_block);
        frame.render_widget(p, ca);
    }
}

fn draw_tasks(frame: &mut Frame, area: Rect, state: &AppState) {
    let block = Block::default()
        .title(" TASKS ")
        .title_style(Style::default().fg(Color::Cyan).bold())
        .borders(Borders::ALL)
        .border_style(panel_border(state.active_panel, Panel::Tasks));

    if state.input_mode == InputMode::TaskCreate {
        let inner = block.inner(area);
        frame.render_widget(block, area);
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([Constraint::Min(1), Constraint::Length(3)])
            .split(inner);

        // Show summary above
        if let Some(ref t) = state.tasks {
            let text = format!("Total: {} | Open: {} | Claimed: {} | Done: {}",
                t.total,
                t.counts.get("open").unwrap_or(&0),
                t.counts.get("claimed").unwrap_or(&0),
                t.counts.get("done").unwrap_or(&0),
            );
            frame.render_widget(
                Paragraph::new(text).style(Style::default().fg(Color::Rgb(120, 120, 150))),
                chunks[0],
            );
        }

        // Task create input
        let input_block = Block::default()
            .title(" New Task (P1) ")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Yellow));
        let cursor = if state.task_input.is_empty() { "task title..." } else { &state.task_input };
        frame.render_widget(
            Paragraph::new(Span::styled(cursor, Style::default().fg(
                if state.task_input.is_empty() { Color::DarkGray } else { Color::White }
            ))).block(input_block),
            chunks[1],
        );
        return;
    }

    let text = if let Some(ref t) = state.tasks {
        let counts = &t.counts;
        let mut lines = vec![
            Line::from(vec![
                Span::styled("Total:   ", Style::default().fg(Color::DarkGray)),
                Span::styled(format!("{}", t.total), Style::default().fg(Color::White).bold()),
            ]),
            Line::from(vec![
                Span::styled("Open:    ", Style::default().fg(Color::DarkGray)),
                Span::styled(format!("{}", counts.get("open").unwrap_or(&0)),
                    Style::default().fg(Color::Green)),
            ]),
            Line::from(vec![
                Span::styled("Claimed: ", Style::default().fg(Color::DarkGray)),
                Span::styled(format!("{}", counts.get("claimed").unwrap_or(&0)),
                    Style::default().fg(Color::Cyan)),
            ]),
            Line::from(vec![
                Span::styled("Done:    ", Style::default().fg(Color::DarkGray)),
                Span::styled(format!("{}", counts.get("done").unwrap_or(&0)),
                    Style::default().fg(Color::DarkGray)),
            ]),
            Line::from(vec![
                Span::styled("Blocked: ", Style::default().fg(Color::DarkGray)),
                Span::styled(format!("{}", counts.get("blocked").unwrap_or(&0)),
                    Style::default().fg(if *counts.get("blocked").unwrap_or(&0) > 0 { Color::Red } else { Color::DarkGray })),
            ]),
        ];
        if !t.active_by_priority.is_empty() {
            let parts: String = t.active_by_priority.iter()
                .map(|(k, v)| format!("{k}={v}")).collect::<Vec<_>>().join(" ");
            lines.push(Line::from(Span::styled(
                format!("Active:  {parts}"), Style::default().fg(Color::Yellow))));
        }
        if let Some(ref claimed) = t.claimed_by_agent {
            lines.push(Line::from(""));
            lines.push(Line::from(Span::styled("By agent:", Style::default().fg(Color::Rgb(80, 80, 110)))));
            for (agent, count) in claimed {
                lines.push(Line::from(vec![
                    Span::styled(format!("  {:<10}", agent), Style::default().fg(Color::White)),
                    Span::styled(format!("{count}"), Style::default().fg(Color::Cyan)),
                ]));
            }
        }
        let stale = t.stale_count.unwrap_or(0);
        if stale > 0 {
            lines.push(Line::from(Span::styled(
                format!("⚠ {stale} stale"), Style::default().fg(Color::Red).bold())));
        }
        Text::from(lines)
    } else {
        Text::styled("No data", Style::default().fg(Color::DarkGray))
    };

    frame.render_widget(Paragraph::new(text).block(block), area);
}

fn draw_task_list(frame: &mut Frame, area: Rect, state: &AppState) {
    let block = Block::default()
        .title(" TASK LIST (l:toggle) ")
        .title_style(Style::default().fg(Color::Cyan).bold())
        .borders(Borders::ALL)
        .border_style(panel_border(state.active_panel, Panel::Tasks));

    if state.task_list.is_empty() {
        frame.render_widget(
            Paragraph::new("No tasks").style(Style::default().fg(Color::DarkGray)).block(block),
            area,
        );
        return;
    }

    let items: Vec<ListItem> = state.task_list.iter().map(|t| {
        let status_color = match t.status.as_str() {
            "open" => Color::Green,
            "claimed" => Color::Cyan,
            "done" => Color::DarkGray,
            "blocked" => Color::Red,
            _ => Color::Gray,
        };
        let pri_color = match t.priority.as_str() {
            "P0" => Color::Red,
            "P1" => Color::Yellow,
            _ => Color::DarkGray,
        };
        let title = if t.title.len() > 40 { format!("{}…", &t.title[..40]) } else { t.title.clone() };
        ListItem::new(Line::from(vec![
            Span::styled(format!("{:<2}", t.priority), Style::default().fg(pri_color)),
            Span::styled(format!(" {:<7}", t.status), Style::default().fg(status_color)),
            Span::styled(format!(" {:<6}", t.agent), Style::default().fg(Color::Rgb(100, 100, 140))),
            Span::styled(format!(" {title}"), Style::default().fg(Color::White)),
        ]))
    }).collect();

    frame.render_widget(List::new(items).block(block), area);
}

fn draw_tribunal(frame: &mut Frame, area: Rect, state: &AppState) {
    let is_input = state.input_mode == InputMode::TribunalInput;
    let block = Block::default()
        .title(" TRIBUNAL ")
        .title_style(Style::default().fg(Color::Cyan).bold())
        .borders(Borders::ALL)
        .border_style(if is_input { Style::default().fg(Color::Yellow) }
            else { panel_border(state.active_panel, Panel::Tribunal) });

    let inner = block.inner(area);
    frame.render_widget(block, area);

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(3), Constraint::Min(1)])
        .split(inner);

    // Input
    let ib = Block::default().borders(Borders::ALL)
        .border_style(Style::default().fg(if is_input { Color::Yellow } else { Color::Rgb(40, 40, 50) }));
    let input_text = if state.tribunal_input.is_empty() && !is_input {
        Paragraph::new(Span::styled("t to evaluate claim...", Style::default().fg(Color::DarkGray)))
    } else {
        Paragraph::new(Span::styled(&state.tribunal_input, Style::default().fg(Color::White)))
    };
    frame.render_widget(input_text.block(ib), chunks[0]);

    // Result
    frame.render_widget(
        Paragraph::new(state.tribunal_result.as_str())
            .style(Style::default().fg(Color::Rgb(180, 180, 200)))
            .wrap(Wrap { trim: true }),
        chunks[1],
    );
}

// ─── Input handling ───────────────────────────────────────────────────

async fn handle_key(state: &mut AppState, key: KeyEvent) {
    match state.input_mode {
        InputMode::Normal => handle_normal(state, key).await,
        InputMode::TribunalInput => handle_text_input(state, key, InputTarget::Tribunal).await,
        InputMode::RadioCompose => handle_text_input(state, key, InputTarget::Radio).await,
        InputMode::TaskCreate => handle_text_input(state, key, InputTarget::Task).await,
    }
}

enum InputTarget { Tribunal, Radio, Task }

async fn handle_text_input(state: &mut AppState, key: KeyEvent, target: InputTarget) {
    match key.code {
        KeyCode::Esc => {
            state.input_mode = InputMode::Normal;
        }
        KeyCode::Enter => {
            match target {
                InputTarget::Tribunal => {
                    let claim = state.tribunal_input.clone();
                    if !claim.trim().is_empty() {
                        state.tribunal_input.clear();
                        state.tribunal_result = "Evaluating...".into();
                        state.input_mode = InputMode::Normal;
                        match submit_tribunal(&state.api_base, &claim).await {
                            Ok(r) => state.tribunal_result = r,
                            Err(e) => state.tribunal_result = format!("Error: {e}"),
                        }
                    }
                }
                InputTarget::Radio => {
                    let msg = state.radio_input.clone();
                    if !msg.trim().is_empty() {
                        state.radio_input.clear();
                        state.input_mode = InputMode::Normal;
                        match send_radio(&state.api_base, &msg).await {
                            Ok(_) => state.status_msg = "radio sent".into(),
                            Err(e) => state.status_msg = format!("radio err: {e}"),
                        }
                        // Refresh radio feed
                        if let Ok(r) = fetch_radio(&state.api_base).await { state.radio = r; }
                    }
                }
                InputTarget::Task => {
                    let title = state.task_input.clone();
                    if !title.trim().is_empty() {
                        state.task_input.clear();
                        state.input_mode = InputMode::Normal;
                        match create_task(&state.api_base, &title).await {
                            Ok(_) => state.status_msg = "task created".into(),
                            Err(e) => state.status_msg = format!("task err: {e}"),
                        }
                        // Refresh tasks
                        if let Ok(t) = fetch_tasks(&state.api_base).await { state.tasks = Some(t); }
                        if state.show_task_list {
                            if let Ok(tl) = fetch_task_list(&state.api_base).await { state.task_list = tl; }
                        }
                    }
                }
            }
        }
        KeyCode::Backspace => {
            match target {
                InputTarget::Tribunal => { state.tribunal_input.pop(); }
                InputTarget::Radio => { state.radio_input.pop(); }
                InputTarget::Task => { state.task_input.pop(); }
            }
        }
        KeyCode::Char(c) => {
            match target {
                InputTarget::Tribunal => state.tribunal_input.push(c),
                InputTarget::Radio => state.radio_input.push(c),
                InputTarget::Task => state.task_input.push(c),
            }
        }
        _ => {}
    }
}

async fn handle_normal(state: &mut AppState, key: KeyEvent) {
    match key.code {
        KeyCode::Char('q') | KeyCode::Char('Q') => state.running = false,
        KeyCode::Char('c') if key.modifiers.contains(KeyModifiers::CONTROL) => state.running = false,

        // Tab: cycle panels
        KeyCode::Tab => {
            let idx = PANELS.iter().position(|p| *p == state.active_panel).unwrap_or(0);
            state.active_panel = PANELS[(idx + 1) % PANELS.len()];
        }
        KeyCode::BackTab => {
            let idx = PANELS.iter().position(|p| *p == state.active_panel).unwrap_or(0);
            state.active_panel = PANELS[(idx + PANELS.len() - 1) % PANELS.len()];
        }

        // Refresh
        KeyCode::Char('r') | KeyCode::Char('R') => {
            state.last_poll = Instant::now() - Duration::from_secs(60);
            state.status_msg = "refreshing...".into();
        }

        // Mode entries
        KeyCode::Char('t') => {
            state.active_panel = Panel::Tribunal;
            state.input_mode = InputMode::TribunalInput;
        }
        KeyCode::Char('m') => {
            state.active_panel = Panel::Radio;
            state.input_mode = InputMode::RadioCompose;
        }
        KeyCode::Char('n') => {
            state.active_panel = Panel::Tasks;
            state.input_mode = InputMode::TaskCreate;
        }
        KeyCode::Char('l') => {
            state.show_task_list = !state.show_task_list;
            if state.show_task_list && state.task_list.is_empty() {
                if let Ok(tl) = fetch_task_list(&state.api_base).await { state.task_list = tl; }
            }
        }

        // Wake all
        KeyCode::Char('w') | KeyCode::Char('W') => {
            let api = state.api_base.clone();
            for agent in ["REX", "ORION", "GEMINI", "HYPERION"] {
                let _ = wake_agent(&api, agent).await;
            }
            state.status_msg = "wake sent to all".into();
        }

        // Navigation (context-dependent)
        KeyCode::Up | KeyCode::Char('k') => match state.active_panel {
            Panel::Agents => {
                if state.agent_cursor > 0 { state.agent_cursor -= 1; }
            }
            Panel::Radio => { state.radio_scroll += 1; }
            Panel::Tasks => { state.task_scroll = state.task_scroll.saturating_sub(1); }
            _ => {}
        },
        KeyCode::Down | KeyCode::Char('j') => match state.active_panel {
            Panel::Agents => {
                if state.agent_cursor + 1 < state.agents.len() { state.agent_cursor += 1; }
            }
            Panel::Radio => { state.radio_scroll = state.radio_scroll.saturating_sub(1); }
            Panel::Tasks => { state.task_scroll += 1; }
            _ => {}
        },

        // Agent actions
        KeyCode::Enter => {
            if state.active_panel == Panel::Agents {
                if let Some(a) = state.selected_agent() {
                    let name = a.name.clone();
                    let _ = wake_agent(&state.api_base, &name).await;
                    state.status_msg = format!("wake {name}");
                }
            }
        }
        KeyCode::Char('p') => {
            if state.active_panel == Panel::Agents {
                if let Some(a) = state.selected_agent() {
                    let name = a.name.clone();
                    let _ = ping_agent(&state.api_base, &name).await;
                    state.status_msg = format!("ping {name}");
                }
            }
        }

        // Home/End for radio
        KeyCode::Home => { state.radio_scroll = state.radio.len(); }
        KeyCode::End => { state.radio_scroll = 0; }

        _ => {}
    }
}

// ─── Main ─────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    let api = std::env::var("RHEA_API").unwrap_or_else(|_| "http://localhost:8400".into());

    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut state = AppState::new(api);
    let poll_interval = Duration::from_secs(5);

    while state.running {
        if state.last_poll.elapsed() >= poll_interval {
            state.last_poll = Instant::now();
            let api = state.api_base.clone();
            match fetch_agents(&api).await {
                Ok(a) => {
                    // Clamp cursor
                    if state.agent_cursor >= a.len() && !a.is_empty() {
                        state.agent_cursor = a.len() - 1;
                    }
                    state.agents = a;
                }
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
            if state.show_task_list {
                if let Ok(tl) = fetch_task_list(&api).await { state.task_list = tl; }
            }
            let alive = state.agents.iter().filter(|a| a.alive).count();
            let total = state.agents.len();
            state.status_msg = format!("{}/{} alive | poll ok", alive, total);
        }

        terminal.draw(|frame| draw(frame, &state))?;

        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                handle_key(&mut state, key).await;
            }
        }
    }

    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    Ok(())
}
