import SwiftUI

/// Proof Store + Ontology browser.
/// Ported from Play macOS → iOS-compatible (no HSplitView).
public struct AletheiaView: View {
    @State private var proofs: [[String: Any]] = []
    @State private var ontologies: [[String: Any]] = []
    @State private var loading = true
    @State private var selectedProof: [String: Any]? = nil
    private let api = RheaAPI.shared

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    summaryBadges
                    if selectedProof != nil {
                        proofDetail
                    }
                    proofList
                    if !ontologies.isEmpty {
                        ontologySection
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }
            .background(RheaTheme.bg)
            .navigationTitle("ALETHEIA")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button { Task { await fetchAll() } } label: {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 13))
                    }
                }
            }
            .task { await fetchAll() }
            .refreshable { await fetchAll() }
            .overlay {
                if loading && proofs.isEmpty {
                    ProgressView().controlSize(.regular)
                }
            }
        }
    }

    // MARK: - Summary

    private var summaryBadges: some View {
        HStack(spacing: 12) {
            badge("PROOFS", "\(proofs.count)", RheaTheme.green)
            badge("ONTOLOGIES", "\(ontologies.count)", RheaTheme.amber)
            Spacer()
        }
    }

    // MARK: - Proof List

    private var proofList: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("PROOF CHAIN")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            ForEach(Array(proofs.enumerated()), id: \.offset) { _, proof in
                Button {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        if selectedProof?["id"] as? String == proof["id"] as? String {
                            selectedProof = nil
                        } else {
                            selectedProof = proof
                        }
                    }
                } label: {
                    HStack(spacing: 10) {
                        let tier = proof["tier"] as? String ?? "?"
                        Text(tier)
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(tierColor(tier))
                            .frame(width: 30)

                        Text(proof["claim"] as? String ?? proof["prompt"] as? String ?? "—")
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.8))
                            .lineLimit(2)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        if let score = proof["agreement_score"] as? Double {
                            Text("\(Int(score * 100))%")
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundStyle(score > 0.7 ? RheaTheme.green : score > 0.4 ? RheaTheme.amber : RheaTheme.red)
                        }

                        Image(systemName: "checkmark.seal.fill")
                            .font(.system(size: 10))
                            .foregroundStyle(RheaTheme.green.opacity(0.5))
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 10)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(selectedProof?["id"] as? String == proof["id"] as? String
                                  ? RheaTheme.accent.opacity(0.1)
                                  : RheaTheme.card.opacity(0.5))
                    )
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Proof Detail (expandable card)

    private var proofDetail: some View {
        Group {
            if let proof = selectedProof {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("PROOF DETAIL")
                            .font(.system(size: 10, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.accent.opacity(0.5))
                        Spacer()
                        Button { withAnimation { selectedProof = nil } } label: {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(.secondary)
                        }
                    }

                    // Claim
                    Text(proof["claim"] as? String ?? proof["prompt"] as? String ?? "—")
                        .font(.system(size: 13, design: .monospaced))
                        .foregroundStyle(.white)
                        .textSelection(.enabled)

                    // Metrics
                    HStack(spacing: 12) {
                        if let score = proof["agreement_score"] as? Double {
                            metricChip("AGREEMENT", "\(Int(score * 100))%", score > 0.7 ? RheaTheme.green : RheaTheme.amber)
                        }
                        if let conf = proof["confidence"] as? Double {
                            metricChip("CONFIDENCE", "\(Int(conf * 100))%", conf > 0.7 ? RheaTheme.green : RheaTheme.amber)
                        }
                        metricChip("TIER", proof["tier"] as? String ?? "?", RheaTheme.accent)
                    }

                    // Verdict
                    if let verdict = proof["verdict"] as? String ?? proof["response"] as? String {
                        Text(verdict)
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.7))
                            .textSelection(.enabled)
                            .lineLimit(10)
                    }

                    // Timestamp
                    if let ts = proof["created_at"] as? String ?? proof["ts"] as? String {
                        Text(ts)
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(.white.opacity(0.3))
                    }
                }
                .padding(14)
                .background(
                    RoundedRectangle(cornerRadius: 10)
                        .fill(RheaTheme.card.opacity(0.6))
                        .overlay(RoundedRectangle(cornerRadius: 10).stroke(RheaTheme.accent.opacity(0.15), lineWidth: 1))
                )
            }
        }
    }

    // MARK: - Ontology Grid

    private var ontologySection: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("ONTOLOGIES")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.5))

            ForEach(Array(ontologies.enumerated()), id: \.offset) { _, ont in
                HStack(spacing: 10) {
                    Image(systemName: "circle.hexagonpath")
                        .font(.system(size: 12))
                        .foregroundStyle(RheaTheme.accent)

                    Text(ont["name"] as? String ?? "—")
                        .font(.system(size: 12, weight: .semibold, design: .monospaced))
                        .foregroundStyle(.white)

                    Spacer()

                    if let count = ont["hypothesis_count"] as? Int {
                        Text("\(count) hyp")
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }

                    if let status = ont["status"] as? String {
                        Text(status.uppercased())
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(status == "active" ? RheaTheme.green : .secondary)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(RheaTheme.card.opacity(0.5))
                )
            }
        }
    }

    // MARK: - Helpers

    private func badge(_ label: String, _ value: String, _ color: Color) -> some View {
        HStack(spacing: 4) {
            Text(label)
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
        }
    }

    private func metricChip(_ label: String, _ value: String, _ color: Color) -> some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.system(size: 14, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
            Text(label)
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(RoundedRectangle(cornerRadius: 8).fill(RheaTheme.card.opacity(0.5)))
    }

    private func tierColor(_ tier: String) -> Color {
        switch tier.lowercased() {
        case "t0": return RheaTheme.green
        case "t1": return RheaTheme.accent
        case "t2": return RheaTheme.amber
        case "t3": return RheaTheme.red
        default: return .secondary
        }
    }

    private func fetchAll() async {
        loading = true
        defer { loading = false }
        proofs = (try? await api.proofs()) ?? []
        ontologies = (try? await api.ontologies()) ?? []
    }
}
