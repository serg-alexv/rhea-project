use super::backend::{RheaUI, InputEvent};
use super::layout::LayoutDef;
use crate::state::AppState;
use crossterm::{
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    Terminal,
    widgets::{Block, Borders, List, ListItem, Paragraph},
    text::Line,
    style::{Color, Style},
    layout::Rect,
};
use std::io;

pub struct RatatuiBackend {
    terminal: Option<Terminal<CrosstermBackend<io::Stdout>>>,
    quit: bool,
}

impl RatatuiBackend {
    pub fn new() -> Self {
        Self {
            terminal: None,
            quit: false,
        }
    }
}

impl RheaUI for RatatuiBackend {
    fn init(&mut self) -> io::Result<()> {
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        execute!(stdout, EnterAlternateScreen)?;

        let backend = CrosstermBackend::new(stdout);
        self.terminal = Some(Terminal::new(backend)?);

        Ok(())
    }

    fn draw(&mut self, state: &AppState) -> io::Result<()> {
        if let Some(terminal) = &mut self.terminal {
            terminal.draw(|f| {
                let [top, bottom] = LayoutDef::main_split(f.size());
                let [events_area, system_area] = LayoutDef::top_split(top);

                // Render events panel
                let events = state.recent_events(20);
                let event_items: Vec<ListItem> = events
                    .iter()
                    .map(|e| {
                        ListItem::new(Line::raw(format!(
                            "[{}] {} → {}",
                            e.actor,
                            e.event_type,
                            e.payload
                                .to_string()
                                .chars()
                                .take(40)
                                .collect::<String>()
                        )))
                    })
                    .collect();

                let events_widget = List::new(event_items)
                    .block(Block::default().title("EVENTS").borders(Borders::ALL));

                f.render_widget(events_widget, events_area);

                // Render system panel
                let status_text = format!(
                    "Daemon: {}\nPort: {}\nLog: {}\n\nActors: {}\nDiscovery: {} nodes",
                    if state.system.daemon_running { "✓ Running" } else { "✗ Stopped" },
                    state.system.daemon_port,
                    if state.system.log_streaming { "✓ Streaming" } else { "✗ Stopped" },
                    state.actors.len(),
                    state.discovery.active_nodes.len()
                );

                let system_widget = Paragraph::new(status_text)
                    .block(Block::default().title("SYSTEM STATE").borders(Borders::ALL))
                    .style(Style::default().fg(Color::Green));

                f.render_widget(system_widget, system_area);

                // Render actors panel
                let actor_items: Vec<ListItem> = state
                    .actors
                    .iter()
                    .map(|(name, actor)| {
                        let color = match actor.status.as_str() {
                            "active" => Color::Green,
                            "idle" => Color::Yellow,
                            _ => Color::Red,
                        };
                        ListItem::new(Line::styled(
                            format!("{}: {} ({} events)", name, actor.status, actor.event_count),
                            Style::default().fg(color),
                        ))
                    })
                    .collect();

                let actors_widget =
                    List::new(actor_items).block(Block::default().title("ACTORS").borders(Borders::ALL));

                f.render_widget(actors_widget, bottom);
            })?;
        }

        Ok(())
    }

    fn handle_event(&mut self, _event: InputEvent) -> io::Result<()> {
        // TODO: Process input events
        Ok(())
    }

    fn shutdown(&mut self) -> io::Result<()> {
        if self.terminal.is_some() {
            disable_raw_mode()?;
            let mut stdout = io::stdout();
            execute!(stdout, LeaveAlternateScreen)?;
            self.terminal = None;
        }
        Ok(())
    }

    fn should_quit(&self) -> bool {
        self.quit
    }
}

impl Default for RatatuiBackend {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ratatui_backend_new() {
        let backend = RatatuiBackend::new();
        assert!(backend.terminal.is_none());
        assert!(!backend.quit);
    }

    #[test]
    fn test_ratatui_backend_default() {
        let backend = RatatuiBackend::default();
        assert!(backend.terminal.is_none());
    }
}
