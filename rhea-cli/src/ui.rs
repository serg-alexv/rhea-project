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
                Constraint::Length(3),
                Constraint::Min(10),
                Constraint::Length(4),
            ])
            .split(f.size());

        // Title
        let title = Paragraph::new("🌟 Rhea Chat — Cross-Device Sessions")
            .alignment(Alignment::Center)
            .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD));
        f.render_widget(title, chunks[0]);

        // Characters
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
            let block = Block::default()
                .borders(Borders::ALL)
                .style(Style::default().fg(character.color()))
                .title(format!(
                    " {} {} — {} ",
                    idx + 1,
                    character.symbol(),
                    character.name()
                ));

            let content = vec![
                Line::from(Span::styled(
                    character.title(),
                    Style::default()
                        .fg(character.color())
                        .add_modifier(Modifier::BOLD),
                )),
                Line::from(""),
                Line::from(Span::raw(format!("  {}", character.description()))),
            ];

            let para = Paragraph::new(content).block(block);
            f.render_widget(para, char_chunks[idx]);
        }

        // Footer
        let footer_text = vec![
            Line::from(Span::raw("Press [1-4] to create session")),
            Line::from(Span::raw("Press [Esc] to quit")),
        ];
        let footer = Paragraph::new(footer_text)
            .style(Style::default().fg(Color::Gray))
            .block(Block::default().borders(Borders::TOP));
        f.render_widget(footer, chunks[2]);
    }

    pub fn render_main(f: &mut Frame, app: &App) {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([Constraint::Min(1), Constraint::Length(3)])
            .split(f.size());

        // Chat area
        let chat_content = if let Some(session) = &app.current_session {
            format!(
                "{} {} Session\nID: {}\nMessages: {}",
                session.character.symbol(),
                session.character.name(),
                session.id,
                session.message_count,
            )
        } else {
            "Loading...".to_string()
        };

        let chat = Paragraph::new(chat_content)
            .style(Style::default().fg(Color::White))
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title(" Chat "),
            );
        f.render_widget(chat, chunks[0]);

        // Input
        let input = format!("YOU: {}", app.input_buffer);
        let input_widget = Paragraph::new(input)
            .style(Style::default().fg(Color::Yellow))
            .block(Block::default().borders(Borders::ALL));
        f.render_widget(input_widget, chunks[1]);
    }
}
