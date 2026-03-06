use crate::state::AppState;
use crossterm::event::KeyCode;

/// Input event for UI backends to handle
#[derive(Clone, Debug)]
pub enum InputEvent {
    Key(KeyCode),
    Mouse { x: u16, y: u16 },
    Resize { width: u16, height: u16 },
    Quit,
}

/// Trait for pluggable UI backends.
/// Implementations: RatatuiBackend, AppCuiBackend, EguiBackend, etc.
pub trait RheaUI {
    /// Initialize the backend (set up terminal, resources, etc.)
    fn init(&mut self) -> std::io::Result<()>;

    /// Draw the UI given the current AppState
    fn draw(&mut self, state: &AppState) -> std::io::Result<()>;

    /// Handle user input event
    fn handle_event(&mut self, event: InputEvent) -> std::io::Result<()>;

    /// Cleanup before shutdown
    fn shutdown(&mut self) -> std::io::Result<()>;

    /// Check if user requested quit
    fn should_quit(&self) -> bool;
}
