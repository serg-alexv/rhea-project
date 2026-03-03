import SwiftUI

/// Full DPI Bypass configuration and monitoring view.
///
/// Provides granular control over every DPIBypassEngine technique:
/// TLS splitting, record splitting, host randomization, fake packets,
/// segment disorder, OOB injection. Stores config in @AppStorage
/// for persistence across launches. No server calls — everything local.
public struct DPIView: View {

    // MARK: - Persisted Config

    @AppStorage("dpi.enabled")              private var enabled = false
    @AppStorage("dpi.splitClientHello")     private var splitClientHello = true
    @AppStorage("dpi.splitSegments")        private var splitSegments = 2
    @AppStorage("dpi.tlsRecordSplit")       private var tlsRecordSplit = false
    @AppStorage("dpi.hostCaseRandomize")    private var hostCaseRandomize = true
    @AppStorage("dpi.fakePacketEnabled")    private var fakePacketEnabled = false
    @AppStorage("dpi.fakePacketTTL")        private var fakePacketTTL = 3
    @AppStorage("dpi.disorder")             private var disorder = false
    @AppStorage("dpi.oobInjection")         private var oobInjection = false
    @AppStorage("dpi.targetDomains")        private var targetDomainsRaw = ""

    // MARK: - Live State

    @State private var newDomain = ""
    @State private var stats = EngineStats()
    @State private var statsTimer: Timer?

    /// Snapshot of engine counters for display.
    private struct EngineStats {
        var totalPackets: UInt64 = 0
        var modifiedPackets: UInt64 = 0
        var tlsClientHellos: UInt64 = 0
        var httpRequests: UInt64 = 0
    }

    private var targetDomains: [String] {
        targetDomainsRaw
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
    }

    public init() {}

    // MARK: - Body

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    statusHeader
                    presetSelector
                    techniqueToggles
                    domainFilter
                    statsCard
                }
                .padding(16)
            }
            .background(RheaTheme.bg)
            .navigationTitle("DPI Bypass")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .onAppear { startStatsPolling() }
            .onDisappear { stopStatsPolling() }
        }
    }

    // MARK: - 1. Status Header

    private var statusHeader: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                HStack(spacing: 6) {
                    Circle()
                        .fill(enabled ? RheaTheme.green : RheaTheme.red)
                        .frame(width: 8, height: 8)
                    Text("DPI ENGINE")
                        .font(.system(size: 11, weight: .bold, design: .monospaced))
                        .foregroundStyle(.white)
                }
                Spacer()
                Toggle("", isOn: $enabled)
                    .labelsHidden()
                    .tint(RheaTheme.accent)
            }

            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("STATUS")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Text(enabled ? "ACTIVE" : "DISABLED")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(enabled ? RheaTheme.green : .secondary)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("MODIFIED")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Text("\(stats.modifiedPackets)")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(stats.modifiedPackets > 0 ? RheaTheme.accent : .secondary)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("TOTAL")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Text("\(stats.totalPackets)")
                        .font(.system(size: 10, weight: .bold, design: .monospaced))
                        .foregroundStyle(.white)
                }
            }
        }
        .glassCard()
    }

    // MARK: - 2. Preset Selector

    private var presetSelector: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("PRESETS")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent)

            HStack(spacing: 10) {
                presetButton("Gentle", icon: "wind") {
                    applyPreset(.gentle)
                }
                presetButton("Aggressive", icon: "bolt.shield") {
                    applyPreset(.aggressive)
                }
            }

            Text("Presets overwrite all technique toggles below.")
                .font(.system(size: 9, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .glassCard()
    }

    private func presetButton(_ label: String, icon: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 11, weight: .bold))
                Text(label.uppercased())
                    .font(.system(size: 11, weight: .bold, design: .monospaced))
            }
            .foregroundStyle(RheaTheme.accent)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 10)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(RheaTheme.accent.opacity(0.1))
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(RheaTheme.accent.opacity(0.3), lineWidth: 1)
                    )
            )
        }
        .buttonStyle(.plain)
    }

    // MARK: - 3. Technique Toggles

    private var techniqueToggles: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("TECHNIQUES")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent)

            // TLS ClientHello splitting
            VStack(alignment: .leading, spacing: 6) {
                techniqueToggle(
                    "TLS ClientHello Splitting",
                    desc: "Fragment ClientHello across TCP segments to hide SNI",
                    isOn: $splitClientHello,
                    color: RheaTheme.green
                )
                if splitClientHello {
                    HStack(spacing: 8) {
                        Text("SEGMENTS")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Stepper("\(splitSegments)", value: $splitSegments, in: 2...5)
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(.white)
                    }
                    .padding(.leading, 20)
                }
            }

            divider

            // TLS record splitting
            techniqueToggle(
                "TLS Record Splitting",
                desc: "Split ClientHello into 2 TLS records within one TCP segment",
                isOn: $tlsRecordSplit,
                color: RheaTheme.green
            )

            divider

            // Host case randomization
            techniqueToggle(
                "Host Case Randomization",
                desc: "hOsT: header defeats regex-based HTTP DPI",
                isOn: $hostCaseRandomize,
                color: RheaTheme.amber
            )

            divider

            // Fake packet injection
            VStack(alignment: .leading, spacing: 6) {
                techniqueToggle(
                    "Fake Packet Injection",
                    desc: "Send fake RST with low TTL to confuse DPI state machine",
                    isOn: $fakePacketEnabled,
                    color: RheaTheme.red
                )
                if fakePacketEnabled {
                    HStack(spacing: 8) {
                        Text("TTL")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Stepper("\(fakePacketTTL)", value: $fakePacketTTL, in: 1...10)
                            .font(.system(size: 11, weight: .bold, design: .monospaced))
                            .foregroundStyle(.white)
                    }
                    .padding(.leading, 20)
                }
            }

            divider

            // Segment disorder
            techniqueToggle(
                "Segment Disorder",
                desc: "Send TCP segments out of order (2,4,6,1,3,5)",
                isOn: $disorder,
                color: Color.purple
            )

            divider

            // OOB injection
            techniqueToggle(
                "OOB Injection",
                desc: "TCP urgent byte after first split — DPI fails to reassemble",
                isOn: $oobInjection,
                color: Color.purple
            )
        }
        .glassCard()
    }

    private func techniqueToggle(_ title: String, desc: String, isOn: Binding<Bool>, color: Color) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Circle()
                    .fill(isOn.wrappedValue ? color : .secondary.opacity(0.3))
                    .frame(width: 6, height: 6)
                Text(title)
                    .font(.system(size: 11, weight: .semibold, design: .monospaced))
                    .foregroundStyle(.white)
                Spacer()
                Toggle("", isOn: isOn)
                    .labelsHidden()
                    .tint(color)
            }
            Text(desc)
                .font(.system(size: 9, design: .monospaced))
                .foregroundStyle(.secondary)
                .padding(.leading, 14)
        }
    }

    private var divider: some View {
        Rectangle()
            .fill(.white.opacity(0.04))
            .frame(height: 1)
    }

    // MARK: - 4. Domain Filter

    private var domainFilter: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("TARGET DOMAINS")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent)

            Text("Empty = apply to all traffic. Add domains to limit scope.")
                .font(.system(size: 9, design: .monospaced))
                .foregroundStyle(.secondary)

            HStack(spacing: 8) {
                TextField("example.com", text: $newDomain)
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundStyle(.white)
                    .padding(8)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(.white.opacity(0.05))
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(.white.opacity(0.1), lineWidth: 1)
                            )
                    )
                    #if os(iOS)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                    #endif
                    .autocorrectionDisabled()

                Button {
                    addDomain()
                } label: {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 20))
                        .foregroundStyle(RheaTheme.accent)
                }
                .buttonStyle(.plain)
                .disabled(newDomain.trimmingCharacters(in: .whitespaces).isEmpty)
            }

            if !targetDomains.isEmpty {
                VStack(spacing: 0) {
                    ForEach(targetDomains, id: \.self) { domain in
                        HStack(spacing: 8) {
                            Circle()
                                .fill(RheaTheme.accent.opacity(0.6))
                                .frame(width: 4, height: 4)
                            Text(domain)
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundStyle(.white)
                            Spacer()
                            Button {
                                removeDomain(domain)
                            } label: {
                                Image(systemName: "xmark.circle")
                                    .font(.system(size: 12))
                                    .foregroundStyle(RheaTheme.red.opacity(0.7))
                            }
                            .buttonStyle(.plain)
                        }
                        .padding(.vertical, 6)
                        .padding(.horizontal, 8)

                        if domain != targetDomains.last {
                            Rectangle()
                                .fill(.white.opacity(0.03))
                                .frame(height: 1)
                        }
                    }
                }
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(.white.opacity(0.03))
                )
            } else {
                HStack {
                    Image(systemName: "globe")
                        .font(.system(size: 10))
                        .foregroundStyle(.secondary)
                    Text("All traffic (no filter)")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
        .glassCard()
    }

    // MARK: - 5. Stats

    private var statsCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("LIVE STATS")
                .font(.system(size: 11, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent)

            HStack(spacing: 0) {
                statColumn("TOTAL", value: "\(stats.totalPackets)", color: .white)
                statColumn("MODIFIED", value: "\(stats.modifiedPackets)", color: RheaTheme.green)
                statColumn("TLS HELLO", value: "\(stats.tlsClientHellos)", color: RheaTheme.accent)
                statColumn("HTTP REQ", value: "\(stats.httpRequests)", color: RheaTheme.amber)
            }

            // Modification ratio bar
            if stats.totalPackets > 0 {
                VStack(alignment: .leading, spacing: 4) {
                    let ratio = Double(stats.modifiedPackets) / Double(stats.totalPackets)
                    HStack {
                        Text("MOD RATIO")
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(String(format: "%.1f%%", ratio * 100))
                            .font(.system(size: 9, weight: .bold, design: .monospaced))
                            .foregroundStyle(RheaTheme.accent)
                    }
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 3)
                                .fill(.white.opacity(0.08))
                            RoundedRectangle(cornerRadius: 3)
                                .fill(RheaTheme.accent)
                                .frame(width: geo.size.width * min(ratio, 1.0))
                                .animation(.easeInOut(duration: 0.4), value: ratio)
                        }
                    }
                    .frame(height: 4)
                }
            }
        }
        .glassCard()
    }

    private func statColumn(_ label: String, value: String, color: Color) -> some View {
        VStack(spacing: 4) {
            Text(value)
                .font(.system(size: 16, weight: .bold, design: .monospaced))
                .foregroundStyle(color)
            Text(label)
                .font(.system(size: 8, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: - Actions

    private func applyPreset(_ preset: DPIBypassEngine.Config) {
        splitClientHello = preset.splitClientHello
        splitSegments = preset.splitSegments
        tlsRecordSplit = preset.tlsRecordSplit
        hostCaseRandomize = preset.hostCaseRandomize
        disorder = preset.disorder
        oobInjection = preset.oobInjection
        fakePacketEnabled = preset.fakePacketTTL != nil
        if let ttl = preset.fakePacketTTL {
            fakePacketTTL = Int(ttl)
        }
        enabled = true
    }

    private func addDomain() {
        let domain = newDomain.trimmingCharacters(in: .whitespaces).lowercased()
        guard !domain.isEmpty else { return }
        var domains = targetDomains
        if !domains.contains(domain) {
            domains.append(domain)
        }
        targetDomainsRaw = domains.joined(separator: ",")
        newDomain = ""
    }

    private func removeDomain(_ domain: String) {
        var domains = targetDomains
        domains.removeAll { $0 == domain }
        targetDomainsRaw = domains.joined(separator: ",")
    }

    /// Build a DPIBypassEngine.Config from current @AppStorage values.
    public func buildConfig() -> DPIBypassEngine.Config {
        var config = DPIBypassEngine.Config()
        config.splitClientHello = splitClientHello
        config.splitSegments = splitSegments
        config.tlsRecordSplit = tlsRecordSplit
        config.hostCaseRandomize = hostCaseRandomize
        config.disorder = disorder
        config.oobInjection = oobInjection
        config.fakePacketTTL = fakePacketEnabled ? UInt8(clamping: fakePacketTTL) : nil
        config.targetDomains = targetDomains
        return config
    }

    // MARK: - Stats Polling

    private func startStatsPolling() {
        // In a real integration, this would read from the running DPIBypassEngine instance
        // via a shared UserDefaults suite or IPC with the packet tunnel extension.
        // For now, poll from engine stats if available.
        statsTimer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { _ in
            refreshStats()
        }
    }

    private func stopStatsPolling() {
        statsTimer?.invalidate()
        statsTimer = nil
    }

    private func refreshStats() {
        // Read from shared UserDefaults (app group) written by the tunnel extension.
        // The extension writes to "group.com.rhea.preview" suite with keys:
        //   dpi_total_packets, dpi_modified_packets, dpi_tls_hellos, dpi_http_requests, dpi_active, dpi_last_update
        let defaults = UserDefaults(suiteName: "group.com.rhea.preview") ?? .standard
        stats.totalPackets = UInt64(defaults.integer(forKey: "dpi_total_packets"))
        stats.modifiedPackets = UInt64(defaults.integer(forKey: "dpi_modified_packets"))
        stats.tlsClientHellos = UInt64(defaults.integer(forKey: "dpi_tls_hellos"))
        stats.httpRequests = UInt64(defaults.integer(forKey: "dpi_http_requests"))
    }
}
