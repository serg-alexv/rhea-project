import SwiftUI

/// SQL-backed tribunal history browser.
/// Reads from /cc/history (persistent, survives restarts).
public struct HistoryView: View {
    @State private var entries: [[String: Any]] = []
    @State private var loading = true
    private let api = RheaAPI.shared

    public init() {}

    public var body: some View {
        NavigationStack {
            Group {
                if loading && entries.isEmpty {
                    ProgressView().controlSize(.regular)
                } else if entries.isEmpty {
                    emptyState
                } else {
                    entryList
                }
            }
            .background(RheaTheme.bg)
            .navigationTitle("HISTORY")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    HStack(spacing: 12) {
                        Text("\(entries.count)")
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Button { Task { await fetch() } } label: {
                            Image(systemName: "arrow.clockwise")
                                .font(.system(size: 13))
                        }
                    }
                }
            }
            .task { await fetch() }
            .refreshable { await fetch() }
        }
    }

    private var entryList: some View {
        ScrollView {
            LazyVStack(spacing: 4) {
                ForEach(Array(entries.enumerated()), id: \.offset) { _, entry in
                    historyRow(entry)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
    }

    private func historyRow(_ entry: [String: Any]) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 10) {
                // Type badge
                Text((entry["type"] as? String ?? "?").uppercased())
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Capsule().fill(RheaTheme.accent.opacity(0.12)))

                Spacer()

                // Agreement score
                if let score = entry["agreement_score"] as? Double {
                    Text("\(Int(score * 100))%")
                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                        .foregroundStyle(score > 0.7 ? RheaTheme.green : score > 0.4 ? RheaTheme.amber : RheaTheme.red)
                }

                // Time
                if let ts = entry["created_at"] as? String, ts.count > 11 {
                    Text(String(ts.dropFirst(11).prefix(5)))
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.3))
                }
            }

            // Prompt
            Text(entry["prompt"] as? String ?? "")
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.white.opacity(0.8))
                .lineLimit(2)

            // Response preview
            if let resp = entry["response"] as? String, !resp.isEmpty {
                Text(resp)
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.4))
                    .lineLimit(1)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(RheaTheme.card.opacity(0.5))
        )
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "clock.arrow.circlepath")
                .font(.system(size: 32))
                .foregroundStyle(.white.opacity(0.15))
            Text("No history yet")
                .font(.system(size: 13, design: .monospaced))
                .foregroundStyle(.white.opacity(0.3))
            Text("Submit a tribunal query to start")
                .font(.system(size: 11, design: .monospaced))
                .foregroundStyle(.white.opacity(0.15))
        }
    }

    private func fetch() async {
        loading = true
        defer { loading = false }
        entries = (try? await api.history(limit: 50)) ?? []
    }
}
