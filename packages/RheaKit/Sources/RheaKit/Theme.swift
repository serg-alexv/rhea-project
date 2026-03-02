import SwiftUI

public enum RheaTheme {
    // MARK: - Colors
    public static let bg = Color(red: 0.06, green: 0.06, blue: 0.10)
    public static let card = Color(red: 0.10, green: 0.10, blue: 0.16)
    public static let cardBorder = Color.white.opacity(0.06)
    public static let accent = Color(red: 0.40, green: 0.85, blue: 1.0)  // cyan
    public static let green = Color(red: 0.30, green: 0.90, blue: 0.50)
    public static let amber = Color(red: 1.0, green: 0.78, blue: 0.20)
    public static let red = Color(red: 1.0, green: 0.35, blue: 0.35)

    // MARK: - Mode colors
    public static func modeColor(_ mode: String) -> Color {
        switch mode {
        case "normal": return green
        case "compact": return amber
        case "critical": return red
        case "hard_fail": return .purple
        default: return .gray
        }
    }

    public static func paceColor(_ pace: String) -> Color {
        switch pace {
        case "green": return green
        case "yellow": return amber
        case "red": return red
        default: return .gray
        }
    }

    public static func priorityColor(_ priority: String) -> Color {
        switch priority {
        case "P0": return red
        case "P1": return amber
        case "P2": return accent
        default: return .gray
        }
    }

    public static func statusColor(_ status: String) -> Color {
        switch status {
        case "open": return .secondary
        case "claimed": return accent
        case "done": return green
        case "blocked": return red
        default: return .gray
        }
    }
}

// MARK: - Card modifier
public struct GlassCard: ViewModifier {
    public init() {}
    public func body(content: Content) -> some View {
        content
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(RheaTheme.card)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(RheaTheme.cardBorder, lineWidth: 1)
                    )
            )
    }
}

public extension View {
    func glassCard() -> some View {
        modifier(GlassCard())
    }
}
