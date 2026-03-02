import SwiftUI

/// Ontology Engine — explore hypothesis spaces and verification chains.
/// Ported from Play macOS → iOS-compatible.
public struct RuliadView: View {
    @State private var ontologies: [[String: Any]] = []
    @State private var selectedOntology: String? = nil
    @State private var hypotheses: [[String: Any]] = []
    @State private var loading = true
    private let api = RheaAPI.shared

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    ontologySelector
                    if selectedOntology != nil {
                        hypothesisSpace
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }
            .background(RheaTheme.bg)
            .navigationTitle("RULIAD")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    HStack(spacing: 8) {
                        if let sel = selectedOntology {
                            Text(sel.uppercased())
                                .font(.system(size: 9, weight: .bold, design: .monospaced))
                                .foregroundStyle(RheaTheme.green)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Capsule().fill(RheaTheme.green.opacity(0.15)))
                        }
                        Button { Task { await fetchOntologies() } } label: {
                            Image(systemName: "arrow.clockwise").font(.system(size: 13))
                        }
                    }
                }
            }
            .task { await fetchOntologies() }
            .refreshable { await fetchOntologies() }
            .overlay {
                if loading && ontologies.isEmpty {
                    ProgressView().controlSize(.regular)
                }
            }
        }
    }

    // MARK: - Ontology Selector

    private var ontologySelector: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("ONTOLOGIES")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            if ontologies.isEmpty && !loading {
                VStack(spacing: 8) {
                    Image(systemName: "function")
                        .font(.system(size: 24))
                        .foregroundStyle(.white.opacity(0.15))
                    Text("No ontologies loaded")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.3))
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 24)
            } else {
                ForEach(Array(ontologies.enumerated()), id: \.offset) { _, ont in
                    let name = ont["name"] as? String ?? "—"
                    Button {
                        selectedOntology = name
                        Task { await fetchHypotheses(name) }
                    } label: {
                        HStack(spacing: 10) {
                            Image(systemName: "circle.hexagonpath")
                                .font(.system(size: 12))
                                .foregroundStyle(selectedOntology == name ? RheaTheme.accent : .secondary)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(name.uppercased())
                                    .font(.system(size: 11, weight: .bold, design: .monospaced))
                                    .foregroundStyle(selectedOntology == name ? .white : .secondary)

                                if let desc = ont["description"] as? String {
                                    Text(desc)
                                        .font(.system(size: 9, design: .monospaced))
                                        .foregroundStyle(.white.opacity(0.3))
                                        .lineLimit(1)
                                }
                            }

                            Spacer()

                            if let count = ont["hypothesis_count"] as? Int, count > 0 {
                                Text("\(count)")
                                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                                    .foregroundStyle(RheaTheme.accent.opacity(0.6))
                            }
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 10)
                        .background(
                            RoundedRectangle(cornerRadius: 8)
                                .fill(selectedOntology == name
                                      ? RheaTheme.accent.opacity(0.1) : RheaTheme.card.opacity(0.5))
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - Hypothesis Space

    private var hypothesisSpace: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("HYPOTHESES")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            if hypotheses.isEmpty {
                VStack(spacing: 8) {
                    Image(systemName: "leaf")
                        .font(.system(size: 24))
                        .foregroundStyle(.white.opacity(0.15))
                    Text("Empty ontology")
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.3))
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 24)
            } else {
                ForEach(Array(hypotheses.enumerated()), id: \.offset) { _, hyp in
                    hypothesisRow(hyp)
                }
            }
        }
    }

    private func hypothesisRow(_ hyp: [String: Any]) -> some View {
        let status = hyp["status"] as? String ?? "proposed"
        return HStack(spacing: 10) {
            Image(systemName: statusIcon(status))
                .font(.system(size: 12))
                .foregroundStyle(statusColor(status))

            Text(hyp["claim"] as? String ?? hyp["hypothesis"] as? String ?? "—")
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.white.opacity(0.8))
                .lineLimit(2)
                .frame(maxWidth: .infinity, alignment: .leading)

            Text(status.uppercased())
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(statusColor(status))
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Capsule().fill(statusColor(status).opacity(0.15)))

            if let conf = hyp["confidence"] as? Double {
                Text("\(Int(conf * 100))%")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(conf > 0.7 ? RheaTheme.green : RheaTheme.amber)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(RheaTheme.card.opacity(0.5))
        )
    }

    // MARK: - Helpers

    private func statusIcon(_ s: String) -> String {
        switch s { case "accepted": return "checkmark.circle.fill"; case "rejected": return "xmark.circle.fill"; case "verified": return "checkmark.seal.fill"; case "proposed": return "questionmark.circle"; default: return "circle" }
    }

    private func statusColor(_ s: String) -> Color {
        switch s { case "accepted", "verified": return RheaTheme.green; case "rejected": return RheaTheme.red; case "proposed": return RheaTheme.amber; default: return .secondary }
    }

    private func fetchOntologies() async {
        loading = true
        defer { loading = false }
        ontologies = (try? await api.ontologies()) ?? []
    }

    private func fetchHypotheses(_ ontology: String) async {
        hypotheses = (try? await api.ontologyDetail(ontology)) ?? []
    }
}
