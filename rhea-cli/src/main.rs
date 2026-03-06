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
use uuid::Uuid;
use std::io;

pub struct App {
    pub client: RheaClient,
    pub selected_char: Option<Character>,
    pub current_session: Option<SessionResponse>,
    pub input_buffer: String,
    pub status: String,
    pub device_id: String,
}

impl App {
    async fn new(server_url: String, device_id: String) -> Result<Self, String> {
        let client = RheaClient::new(server_url, ":memory:")
            .await
            .map_err(|e| e.to_string())?;
        
        Ok(App {
            client,
            selected_char: None,
            current_session: None,
            input_buffer: String::new(),
            status: format!("Device: {} | Type /help for commands", &device_id[0..8.min(device_id.len())]),
            device_id,
        })
    }

    async fn create_session(&mut self, char_name: &str) -> Result<(), String> {
        let character = rhea_session_server::Character::Protos; // Will be set by char_name
        let character = match char_name {
            "PROTOS" => rhea_session_server::Character::Protos,
            "ZERG" => rhea_session_server::Character::Zerg,
            "TERRAN" => rhea_session_server::Character::Terran,
            "AEON" => rhea_session_server::Character::Aeon,
            _ => rhea_session_server::Character::Protos,
        };
        
        let session = self.client.create_session(character).await?;
        let session_id = session.id;
        self.current_session = Some(session);
        self.selected_char = Some(Character::from_str(char_name));
        self.status = format!("Session: {} | Device: {}", 
            &session_id.to_string()[0..8.min(36)],
            &self.device_id[0..8.min(self.device_id.len())]
        );
        Ok(())
    }

    async fn send_message(&mut self, content: String) -> Result<(), String> {
        if content.starts_with('/') {
            self.handle_command(&content).await
        } else if let Some(session) = &self.current_session {
            self.client.add_message(session.id, "user".to_string(), content).await?;
            self.input_buffer.clear();
            Ok(())
        } else {
            Err("No session active".to_string())
        }
    }

    async fn handle_command(&mut self, cmd: &str) -> Result<(), String> {
        match cmd {
            "/help" => {
                help::show_help();
                Ok(())
            }
            "/device" => {
                println!("Device ID: {}", self.device_id);
                Ok(())
            }
            _ => Err(format!("Unknown command: {}", cmd))
        }
    }
}

#[tokio::main]
async fn main() -> io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    
    // Check for command-line help
    if args.len() > 1 {
        match args[1].as_str() {
            "--help" => {
                help::show_help();
                return Ok(());
            }
            _ => {}
        }
    }

    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let res = run_app(&mut terminal).await;

    // Restore terminal
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
    
    // Try to init app
    let mut app = match App::new(server_url.clone(), device_id.clone()).await {
        Ok(a) => a,
        Err(e) => {
            // Show error in terminal
            terminal.draw(|f| {
                let msg = format!("❌ Failed to connect to server at {}\n\nError: {}\n\nMake sure to run:\n  cargo run --release -p rhea-session-server", server_url, e);
                let para = Paragraph::new(msg)
                    .style(Style::default().fg(Color::Red));
                let area = f.size();
                f.render_widget(para, area);
            })?;
            
            // Wait for any key to exit
            std::thread::sleep(std::time::Duration::from_secs(3));
            return Ok(());
        }
    };

    let mut status_timer = 0u64;

    loop {
        terminal.draw(|f| {
            if app.selected_char.is_none() {
                ui::UIRenderer::render_character_select(f);
            } else {
                ui::UIRenderer::render_main(f, &app);
            }
        })?;

        if crossterm::event::poll(std::time::Duration::from_millis(50))? {
            if let Event::Key(key) = event::read()? {
                match (key.code, key.modifiers) {
                    (KeyCode::Char('c'), KeyModifiers::CONTROL) => return Ok(()),
                    (KeyCode::Esc, _) => {
                        if app.selected_char.is_some() {
                            app.selected_char = None;
                            app.current_session = None;
                            app.input_buffer.clear();
                        } else {
                            return Ok(());
                        }
                    }
                    (KeyCode::Char(c), _) if app.selected_char.is_none() => {
                        match c {
                            '1' => {
                                if let Err(e) = app.create_session("PROTOS").await {
                                    app.status = format!("Error: {}", e);
                                }
                            }
                            '2' => {
                                if let Err(e) = app.create_session("ZERG").await {
                                    app.status = format!("Error: {}", e);
                                }
                            }
                            '3' => {
                                if let Err(e) = app.create_session("TERRAN").await {
                                    app.status = format!("Error: {}", e);
                                }
                            }
                            '4' => {
                                if let Err(e) = app.create_session("AEON").await {
                                    app.status = format!("Error: {}", e);
                                }
                            }
                            _ => {}
                        }
                    }
                    (KeyCode::Char(c), _) if app.selected_char.is_some() => {
                        app.input_buffer.push(c);
                    }
                    (KeyCode::Enter, _) if app.selected_char.is_some() => {
                        if !app.input_buffer.is_empty() {
                            let msg = app.input_buffer.clone();
                            if let Err(e) = app.send_message(msg).await {
                                app.status = format!("Error: {}", e);
                            } else {
                                app.status.clear();
                            }
                        }
                    }
                    (KeyCode::Backspace, _) => {
                        app.input_buffer.pop();
                    }
                    _ => {}
                }
            }
        }
    }
}
