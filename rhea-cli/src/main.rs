mod character;
mod ui;
mod help;

use character::Character;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyModifiers},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal, style::{Color, Style}, widgets::Paragraph};
use rhea_client::RheaClient;
use rhea_session_server::SessionResponse;
use std::io;
use tokio::sync::mpsc;
use std::sync::Arc;

#[derive(Clone, Debug)]
enum BackgroundTask {
    CreateSession(String),
    SendMessage(String),
}

#[derive(Clone, Debug)]
enum TaskResult {
    SessionCreated(SessionResponse),
    SessionFailed(String),
    MessageSent,
    MessageFailed(String),
}

pub struct App {
    pub client: Arc<RheaClient>,
    pub selected_char: Option<Character>,
    pub current_session: Option<SessionResponse>,
    pub input_buffer: String,
    pub status: String,
    pub device_id: String,
    pub is_loading: bool,
}

impl App {
    async fn new(server_url: String, device_id: String) -> Result<Self, String> {
        let client = RheaClient::new(server_url, ":memory:")
            .await
            .map_err(|e| e.to_string())?;
        
        Ok(App {
            client: Arc::new(client),
            selected_char: None,
            current_session: None,
            input_buffer: String::new(),
            status: format!("Device: {} | Press 1-4", &device_id[0..8.min(device_id.len())]),
            device_id,
            is_loading: false,
        })
    }
}

#[tokio::main]
async fn main() -> io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() > 1 {
        match args[1].as_str() {
            "--help" => {
                help::show_help();
                return Ok(());
            }
            _ => {}
        }
    }

    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let res = run_app(&mut terminal).await;

    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    if let Err(err) = res {
        eprintln!("Error: {}", err);
    }

    Ok(())
}

async fn run_app<B: ratatui::backend::Backend>(
    terminal: &mut Terminal<B>,
) -> io::Result<()> {
    let device_id = uuid::Uuid::new_v4().to_string();
    let server_url = std::env::var("RHEA_SERVER").unwrap_or_else(|_| "http://127.0.0.1:3000".to_string());
    
    let mut app = match App::new(server_url.clone(), device_id.clone()).await {
        Ok(a) => a,
        Err(e) => {
            terminal.draw(|f| {
                let msg = format!("❌ Failed to connect to server at {}\n\nError: {}\n\nMake sure to run:\n  cargo run --release -p rhea-session-server", server_url, e);
                let para = Paragraph::new(msg)
                    .style(Style::default().fg(Color::Red));
                let area = f.size();
                f.render_widget(para, area);
            })?;
            
            std::thread::sleep(std::time::Duration::from_secs(3));
            return Ok(());
        }
    };

    // Channel for background task results
    let (tx, mut rx) = mpsc::channel(10);

    loop {
        // Check for background task results (non-blocking)
        tokio::select! {
            Some(result) = rx.recv() => {
                match result {
                    TaskResult::SessionCreated(session) => {
                        app.current_session = Some(session.clone());
                        app.selected_char = Some(Character::from_str(&session.character));
                        app.status = format!("Session created! Type message...");
                        app.is_loading = false;
                    }
                    TaskResult::SessionFailed(err) => {
                        app.status = format!("Error: {}", err);
                        app.is_loading = false;
                    }
                    TaskResult::MessageSent => {
                        app.status = "Message sent ✓".to_string();
                        app.is_loading = false;
                    }
                    TaskResult::MessageFailed(err) => {
                        app.status = format!("Error: {}", err);
                        app.is_loading = false;
                    }
                }
            }
            _ = tokio::time::sleep(tokio::time::Duration::from_millis(30)) => {
                // Timeout every 30ms to check for keyboard input
            }
        }

        terminal.draw(|f| {
            if app.selected_char.is_none() {
                ui::UIRenderer::render_character_select(f);
            } else {
                ui::UIRenderer::render_main(f, &app);
            }
        })?;

        // Non-blocking event poll
        if crossterm::event::poll(std::time::Duration::from_millis(10))? {
            if let Event::Key(key) = event::read()? {
                match (key.code, key.modifiers) {
                    (KeyCode::Char('c'), KeyModifiers::CONTROL) => return Ok(()),
                    (KeyCode::Esc, _) => {
                        if app.selected_char.is_some() {
                            app.selected_char = None;
                            app.current_session = None;
                            app.input_buffer.clear();
                            app.status = "Back to character select".to_string();
                        } else {
                            return Ok(());
                        }
                    }
                    // Character selection - spawn background task
                    (KeyCode::Char(c), _) if app.selected_char.is_none() && !app.is_loading => {
                        let char_name = match c {
                            '1' => Some("PROTOS"),
                            '2' => Some("ZERG"),
                            '3' => Some("TERRAN"),
                            '4' => Some("AEON"),
                            _ => None,
                        };
                        
                        if let Some(char_name) = char_name {
                            app.is_loading = true;
                            app.status = format!("⟳ Creating {} session...", char_name);
                            
                            let client = app.client.clone();
                            let tx = tx.clone();
                            let char_name = char_name.to_string();
                            
                            tokio::spawn(async move {
                                let character = match char_name.as_str() {
                                    "PROTOS" => rhea_session_server::Character::Protos,
                                    "ZERG" => rhea_session_server::Character::Zerg,
                                    "TERRAN" => rhea_session_server::Character::Terran,
                                    "AEON" => rhea_session_server::Character::Aeon,
                                    _ => rhea_session_server::Character::Protos,
                                };
                                
                                match client.create_session(character).await {
                                    Ok(session) => {
                                        let _ = tx.send(TaskResult::SessionCreated(session)).await;
                                    }
                                    Err(e) => {
                                        let _ = tx.send(TaskResult::SessionFailed(e)).await;
                                    }
                                }
                            });
                        }
                    }
                    // Message input - instant echo (no blocking)
                    (KeyCode::Char(c), _) if app.selected_char.is_some() && !app.is_loading => {
                        app.input_buffer.push(c);
                    }
                    // Send message
                    (KeyCode::Enter, _) if app.selected_char.is_some() && !app.input_buffer.is_empty() && !app.is_loading => {
                        let msg = app.input_buffer.clone();
                        app.input_buffer.clear();
                        app.is_loading = true;
                        app.status = "⟳ Sending...".to_string();
                        
                        if let Some(session) = app.current_session.clone() {
                            let client = app.client.clone();
                            let tx = tx.clone();
                            
                            tokio::spawn(async move {
                                match client.add_message(session.id, "user".to_string(), msg).await {
                                    Ok(_) => {
                                        let _ = tx.send(TaskResult::MessageSent).await;
                                    }
                                    Err(e) => {
                                        let _ = tx.send(TaskResult::MessageFailed(e)).await;
                                    }
                                }
                            });
                        }
                    }
                    // Backspace
                    (KeyCode::Backspace, _) if !app.input_buffer.is_empty() => {
                        app.input_buffer.pop();
                    }
                    _ => {}
                }
            }
        }
    }
}
