use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
    Frame,
};

use crate::{character::Character, App};

pub struct UIRenderer;

impl UIRenderer {
    pub fn render_character_select(f: &mut Frame) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(2),
                Constraint::Min(8),
                Constraint::Length(3),
            ])
            .split(f.size());

        // Title with emphasis
        let title = Paragraph::new("🌟 Rhea Chat — Cross-Device Sessions")
            .alignment(Alignment::Center)
            .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD));
        f.render_widget(title, chunks[0]);

        // Characters with enhanced styling
        let char_chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Length(5),
                Constraint::Length(5),
                Constraint::Length(5),
                Constraint::Length(5),
            ])
            .split(chunks[1]);

        for (idx, character) in Character::all().iter().enumerate() {
            let color = character.color();
            let block = Block::default()
                .borders(Borders::ALL)
                .style(Style::default().fg(color))
                .title(format!(
                    " {} {} — {} ",
                    idx + 1,
                    character.symbol(),
                    character.name()
                ))
                .border_style(Style::default().fg(color).add_modifier(Modifier::BOLD));

            let content = vec![
                Line::from(Span::styled(
                    character.title(),
                    Style::default()
                        .fg(color)
                        .add_modifier(Modifier::BOLD),
                )),
                Line::from(""),
                Line::from(Span::styled(
                    format!("  {}", character.description()),
                    Style::default().fg(Color::Gray),
                )),
            ];

            let para = Paragraph::new(content).block(block);
            f.render_widget(para, char_chunks[idx]);
        }

        // Footer with clear instructions
        let footer_text = vec![
            Line::from(Span::styled(
                "Press [1-4] to select character • [Esc] to quit",
                Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
            )),
        ];
        let footer = Paragraph::new(footer_text)
            .alignment(Alignment::Center)
            .style(Style::default().fg(Color::Gray))
            .block(Block::default().borders(Borders::TOP));
        f.render_widget(footer, chunks[2]);
    }

    pub fn render_main(f: &mut Frame, app: &App) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([Constraint::Min(1), Constraint::Length(4)])
            .split(f.size());

        // Session header with live character info
        let header = if let Some(session) = &app.current_session {
            let char_local = Character::from_str(&session.character);
            vec![
                Line::from(Span::styled(
                    format!("{} {} — Cross-Device Session", char_local.symbol(), char_local.name()),
                    Style::default()
                        .fg(char_local.color())
                        .add_modifier(Modifier::BOLD),
                )),
                Line::from(Span::raw(format!(
                    "├─ Messages: {} | Device: {} | ID: {}",
                    session.message_count,
                    &app.device_id[0..8.min(app.device_id.len())],
                    &session.id.to_string()[0..8.min(36)]
                ))),
            ]
        } else {
            vec![
                Line::from(Span::styled(
                    "⟳ Loading session...",
                    Style::default().fg(Color::Gray),
                )),
            ]
        };

        let header_widget = Paragraph::new(header)
            .style(Style::default().fg(Color::White))
            .block(Block::default().borders(Borders::BOTTOM));
        f.render_widget(header_widget, chunks[0]);

        // Input area with live preview
        let input_color = if app.input_buffer.is_empty() {
            Color::Gray
        } else {
            Color::Green
        };

        let input_preview = if app.input_buffer.is_empty() {
            "Type message (Enter to send, Esc to back)...".to_string()
        } else {
            format!("{}", app.input_buffer)
        };

        let input_lines = vec![
            Line::from(Span::styled(
                "✏️  Message:",
                Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
            )),
            Line::from(Span::styled(
                input_preview,
                Style::default().fg(input_color),
            )),
            Line::from(Span::raw(&app.status)),
        ];

        let input_widget = Paragraph::new(input_lines)
            .style(Style::default().fg(Color::White))
            .block(Block::default().borders(Borders::ALL).title(" Input "));
        f.render_widget(input_widget, chunks[1]);
    }
}
