use ratatui::layout::{Constraint, Direction, Layout, Rect};

/// Define the cockpit 3-panel layout
/// Top: 70% (events left, system right)
/// Bottom: 30% (actors)
pub struct LayoutDef;

impl LayoutDef {
    /// Get main vertical split: [top_section, bottom_section]
    pub fn main_split(area: Rect) -> [Rect; 2] {
        let layout = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Percentage(70),
                Constraint::Percentage(30),
            ])
            .split(area);

        [layout[0], layout[1]]
    }

    /// Get horizontal split of top section: [events_panel, system_panel]
    pub fn top_split(area: Rect) -> [Rect; 2] {
        let layout = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([
                Constraint::Percentage(50),
                Constraint::Percentage(50),
            ])
            .split(area);

        [layout[0], layout[1]]
    }

    /// Subdivide for borders and padding
    /// Returns: [header, content_area]
    pub fn panel_split(area: Rect, with_header: bool) -> Option<[Rect; 2]> {
        if area.height < 3 {
            return None;
        }

        let layout = Layout::default()
            .direction(Direction::Vertical)
            .constraints(if with_header {
                vec![Constraint::Length(1), Constraint::Min(1)]
            } else {
                vec![Constraint::Min(1)]
            })
            .split(area);

        Some([layout[0], layout[1]])
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_main_split() {
        let area = Rect {
            x: 0,
            y: 0,
            width: 100,
            height: 100,
        };

        let [top, bottom] = LayoutDef::main_split(area);

        assert_eq!(top.height, 70);
        assert_eq!(bottom.height, 30);
    }

    #[test]
    fn test_top_split() {
        let area = Rect {
            x: 0,
            y: 0,
            width: 100,
            height: 70,
        };

        let [left, right] = LayoutDef::top_split(area);

        assert_eq!(left.width, 50);
        assert_eq!(right.width, 50);
    }
}
