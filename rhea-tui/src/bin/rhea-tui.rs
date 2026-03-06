use rhea_tui::{
    events::parse_event,
    state::{AppState, reduce},
    ui::RheaUI,
};
use rhea_tui::ui::ratatui_impl::RatatuiBackend;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;
use std::time::Duration;
use std::thread;

fn main() -> std::io::Result<()> {
    // Parse command-line arguments
    let args: Vec<String> = std::env::args().collect();
    let log_path = if args.len() > 1 {
        &args[1]
    } else {
        "/tmp/0.log"
    };

    // Initialize UI backend (currently only ratatui)
    let mut ui = RatatuiBackend::new();
    ui.init()?;

    // Application state
    let mut state = AppState::new();

    // If log file exists, load initial events
    if Path::new(log_path).exists() {
        if let Ok(file) = File::open(log_path) {
            let reader = BufReader::new(file);
            for line in reader.lines() {
                if let Ok(line) = line {
                    if !line.trim().is_empty() {
                        let event = parse_event(&line);
                        reduce(&mut state, &event);
                    }
                }
            }
        }
    }

    // Main loop: read log → parse → reduce → draw
    println!("Cockpit starting. Log path: {}", log_path);
    thread::sleep(Duration::from_millis(100));

    loop {
        // Draw current state
        ui.draw(&state)?;

        // Check for quit
        if ui.should_quit() {
            break;
        }

        // Sleep briefly to prevent busy-waiting
        thread::sleep(Duration::from_millis(100));
    }

    // Cleanup
    ui.shutdown()?;
    println!("Cockpit shutdown gracefully");

    Ok(())
}
