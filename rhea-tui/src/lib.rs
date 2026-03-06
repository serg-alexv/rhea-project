pub mod events;
pub mod state;
pub mod ui;

// Public exports for easy access
pub use events::{Event, parse_event};
pub use state::{AppState, reduce};
pub use ui::{RheaUI, InputEvent, LayoutDef};
