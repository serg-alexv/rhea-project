import SwiftUI

/// Shows messages between agents — the internal communication channel.
/// Reads from /cc/office (public, no auth needed).
public struct OfficeView: View {
    @StateObject private var store = RheaStore.shared
    @State private var messages: [[String: Any]] = []
    @State private var isLoading = false

    public init() {}

    public var body: some View {
        NavigationStack {
            Group {
                if isLoading && messages.isEmpty {
                    ProgressView("Loading messages...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if messages.isEmpty {
                    VStack(spacing: 8) {
                        Image(systemName: "bubble.left.and.bubble.right")
                            .font(.system(size: 32))
                            .foregroundStyle(.secondary)
                        Text("No messages yet")
                            .font(.system(size: 13, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    ScrollView {
                        LazyVStack(spacing: 8) {
                            ForEach(Array(messages.enumerated()), id: \.offset) { _, msg in
                                messageRow(msg)
                            }
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                    }
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("Office")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button(action: { Task { await refresh() } }) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 13))
                    }
                }
            }
            .task { await refresh() }
        }
    }

    private func messageRow(_ msg: [String: Any]) -> some View {
        let sender = msg["sender"] as? String ?? "?"
        let receiver = msg["receiver"] as? String ?? "?"
        let text = msg["text"] as? String ?? ""
        let ts = msg["ts"] as? String ?? ""
        let displayTime = String(ts.suffix(from: ts.index(ts.startIndex, offsetBy: min(11, ts.count), limitedBy: ts.endIndex) ?? ts.startIndex).prefix(5))

        return VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 6) {
                Text(sender)
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent)
                Image(systemName: "arrow.right")
                    .font(.system(size: 9))
                    .foregroundStyle(.secondary)
                Text(receiver)
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.amber)
                Spacer()
                Text(displayTime)
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.secondary)
            }
            Text(text)
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.white.opacity(0.85))
                .lineLimit(4)
        }
        .padding(10)
        .background(
            RoundedRectangle(cornerRadius: 10)
                .fill(RheaTheme.card)
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(RheaTheme.cardBorder, lineWidth: 1)
                )
        )
    }

    private func refresh() async {
        isLoading = true
        messages = await store.refreshOffice(limit: 50)
        isLoading = false
    }
}
