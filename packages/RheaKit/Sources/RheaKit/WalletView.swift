import SwiftUI

/// Crypto wallet — donation addresses, balance check, QR codes.
/// Reads from /wallet/status (public addresses only, no private keys).
public struct WalletView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var wallets: [[String: Any]] = []
    @State private var btcBalance: String?
    @State private var isLoading = false
    @State private var copiedAddress: String?

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    if wallets.isEmpty && !isLoading {
                        VStack(spacing: 8) {
                            Image(systemName: "creditcard.trianglebadge.exclamationmark")
                                .font(.system(size: 32))
                                .foregroundStyle(.secondary)
                            Text("No wallets configured")
                                .font(.system(size: 13, design: .monospaced))
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.top, 60)
                    }

                    ForEach(Array(wallets.enumerated()), id: \.offset) { _, wallet in
                        walletCard(wallet)
                    }

                    if !wallets.isEmpty {
                        infoCard
                    }
                }
                .padding(16)
            }
            .background(RheaTheme.bg)
            .navigationTitle("Wallet")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button { loadWallets() } label: {
                        Image(systemName: "arrow.clockwise")
                            .foregroundColor(RheaTheme.accent)
                    }
                }
            }
            .task { loadWallets() }
        }
    }

    private func walletCard(_ wallet: [String: Any]) -> some View {
        let chain = wallet["chain"] as? String ?? "?"
        let address = wallet["address"] as? String ?? ""
        let label = wallet["label"] as? String ?? chain.uppercased()
        let network = wallet["network"] as? String ?? ""

        return VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: chainIcon(chain))
                    .font(.system(size: 16))
                    .foregroundStyle(chainColor(chain))
                    .frame(width: 24)
                Text(label)
                    .font(.system(size: 12, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)
                Spacer()
                Text(network.uppercased())
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Capsule().fill(RheaTheme.card))
            }

            // Address
            Button {
                #if os(iOS)
                UIPasteboard.general.string = address
                #else
                NSPasteboard.general.clearContents()
                NSPasteboard.general.setString(address, forType: .string)
                #endif
                copiedAddress = address
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) { copiedAddress = nil }
            } label: {
                HStack(spacing: 6) {
                    Text(address)
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(RheaTheme.accent)
                        .lineLimit(1)
                        .truncationMode(.middle)
                    Image(systemName: copiedAddress == address ? "checkmark" : "doc.on.doc")
                        .font(.system(size: 10))
                        .foregroundStyle(copiedAddress == address ? RheaTheme.green : .secondary)
                }
            }
            .buttonStyle(.plain)

            // Balance (BTC only for now)
            if chain == "btc" {
                HStack(spacing: 6) {
                    Text("BALANCE")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    if let bal = btcBalance {
                        Text(bal)
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.green)
                    } else {
                        Button("Check") { checkBalance(chain: "btc") }
                            .font(.system(size: 10, weight: .semibold, design: .monospaced))
                            .foregroundStyle(RheaTheme.accent)
                    }
                }
            }
        }
        .glassCard()
    }

    private var infoCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("ABOUT")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
            Text("These are public donation addresses for the timelabs npo project. Tap an address to copy. No private keys are exposed through this interface.")
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
        }
        .glassCard()
    }

    private func chainIcon(_ chain: String) -> String {
        switch chain {
        case "btc": return "bitcoinsign.circle"
        case "eth": return "diamond"
        case "usdt": return "dollarsign.circle"
        default: return "creditcard"
        }
    }

    private func chainColor(_ chain: String) -> Color {
        switch chain {
        case "btc": return .orange
        case "eth": return .purple
        case "usdt": return RheaTheme.green
        default: return RheaTheme.accent
        }
    }

    private func loadWallets() {
        isLoading = true
        guard let url = URL(string: "\(apiBaseURL)/wallet/status") else { return }
        URLSession.shared.dataTask(with: url) { data, _, _ in
            defer { DispatchQueue.main.async { isLoading = false } }
            guard let data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let list = json["wallets"] as? [[String: Any]] else { return }
            DispatchQueue.main.async { wallets = list }
        }.resume()
    }

    private func checkBalance(chain: String) {
        guard let url = URL(string: "\(apiBaseURL)/wallet/balance/\(chain)") else { return }
        URLSession.shared.dataTask(with: url) { data, _, _ in
            guard let data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
            DispatchQueue.main.async {
                if let bal = json["balance"] as? Double {
                    btcBalance = String(format: "%.8f BTC", bal)
                } else {
                    btcBalance = "0.00000000 BTC"
                }
            }
        }.resume()
    }
}
