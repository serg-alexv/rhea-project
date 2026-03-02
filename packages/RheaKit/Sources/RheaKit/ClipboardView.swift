import SwiftUI

struct ClipEntry: Identifiable, Codable {
    let id: String, content: String, contentType: String, contentPreview: String?
    let deviceName: String, privacy: String, pinned: Bool
    let createdAt: String, expiresAt: String?
    enum CodingKeys: String, CodingKey {
        case id, content, privacy, pinned
        case contentType = "content_type", contentPreview = "content_preview"
        case deviceName = "device_name", createdAt = "created_at", expiresAt = "expires_at"
    }
}

private struct ClipListResponse: Codable { let clips: [ClipEntry] }

public struct ClipboardView: View {
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL
    @State private var clips: [ClipEntry] = []
    @State private var isLoading = false
    @State private var errorText: String? = nil
    @State private var showCopiedToast = false
    @State private var copiedClipId: String? = nil
    @State private var pollTimer: Timer? = nil
    @State private var connected = false
    @State private var isPushing = false

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 12) {
                    statusBar
                    pushCurrentSection
                    historySection
                    if !clips.isEmpty { clearButton }
                }
                .padding(.horizontal, 12).padding(.bottom, 20)
            }
            .background(RheaTheme.bg)
            .navigationTitle("Clipboard")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            .toolbarColorScheme(.dark, for: .navigationBar)
            #endif
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button { Task { await fetchClips() } } label: {
                        Image(systemName: "arrow.clockwise").foregroundStyle(RheaTheme.accent)
                    }
                }
            }
            .refreshable { await fetchClips() }
            .task { await fetchClips(); startPolling() }
            .onDisappear { stopPolling() }
            .overlay(alignment: .top) {
                if showCopiedToast {
                    Text("Copied!")
                        .font(.system(size: 13, weight: .semibold, design: .monospaced))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 16).padding(.vertical, 8)
                        .background(Capsule().fill(RheaTheme.green.opacity(0.85)))
                        .transition(.move(edge: .top).combined(with: .opacity))
                        .padding(.top, 8)
                }
            }
        }
    }

    // MARK: - Status Bar
    private var statusBar: some View {
        HStack(spacing: 10) {
            Circle().fill(connected ? RheaTheme.green : RheaTheme.red).frame(width: 8, height: 8)
            Text(connected ? "CONNECTED" : "OFFLINE")
                .font(.system(size: 9, weight: .bold, design: .monospaced))
                .foregroundStyle(connected ? RheaTheme.green : RheaTheme.red)
            Spacer()
            Text("Device: \(currentDeviceName)")
                .font(.system(size: 10, design: .monospaced)).foregroundStyle(.secondary)
        }
        .glassCard()
    }

    // MARK: - Push Current
    private var pushCurrentSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionHeader("PUSH CURRENT", icon: "arrow.up.doc")
            let local = localClipboardContent
            if let text = local, !text.isEmpty {
                Text(text.prefix(120) + (text.count > 120 ? "..." : ""))
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.75)).lineLimit(3)
                Button { Task { await pushClipboard(text) } } label: {
                    HStack(spacing: 6) {
                        if isPushing {
                            ProgressView().tint(.white).controlSize(.small)
                        } else {
                            Image(systemName: "icloud.and.arrow.up").font(.system(size: 11))
                        }
                        Text("Sync to server")
                            .font(.system(size: 11, weight: .medium, design: .monospaced))
                    }
                    .foregroundStyle(.white)
                    .padding(.horizontal, 14).padding(.vertical, 8)
                    .background(Capsule().fill(RheaTheme.accent.opacity(0.3)))
                    .overlay(Capsule().stroke(RheaTheme.accent.opacity(0.5), lineWidth: 1))
                }
                .buttonStyle(.plain).disabled(isPushing)
            } else {
                Text("Clipboard empty")
                    .font(.system(size: 11, design: .monospaced)).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center).padding(.vertical, 4)
            }
        }
        .glassCard()
    }

    // MARK: - History
    private var historySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionHeader("HISTORY", icon: "clock.arrow.circlepath")
            if isLoading && clips.isEmpty {
                ProgressView().tint(RheaTheme.accent)
                    .frame(maxWidth: .infinity).padding(.vertical, 12)
            } else if clips.isEmpty {
                Text("No clipboard history yet")
                    .font(.system(size: 11, design: .monospaced)).foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center).padding(.vertical, 12)
            } else {
                ForEach(clips) { clip in clipRow(clip) }
            }
        }
        .glassCard()
    }

    private func clipRow(_ clip: ClipEntry) -> some View {
        Button { copyToLocal(clip) } label: {
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 6) {
                    Text(typeIcon(clip.contentType)).font(.system(size: 12))
                    let display = clip.privacy == "secret"
                        ? (clip.contentPreview ?? "[redacted]")
                        : String(clip.content.prefix(100))
                    Text(display)
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.85))
                        .lineLimit(2).multilineTextAlignment(.leading)
                    Spacer()
                }
                HStack(spacing: 8) {
                    Text(clip.deviceName).font(.system(size: 9, design: .monospaced)).foregroundStyle(.secondary)
                    Text(relativeTime(clip.createdAt)).font(.system(size: 9, design: .monospaced)).foregroundStyle(.secondary)
                    Spacer()
                    if clip.pinned {
                        Image(systemName: "pin.fill").font(.system(size: 9)).foregroundStyle(RheaTheme.amber)
                    }
                    privacyBadge(clip)
                    if let exp = clip.expiresAt, !exp.isEmpty {
                        Text("exp").font(.system(size: 8, weight: .bold, design: .monospaced)).foregroundStyle(RheaTheme.red)
                    }
                }
            }
            .padding(10)
            .background(
                RoundedRectangle(cornerRadius: 10).fill(.white.opacity(0.04))
                    .overlay(RoundedRectangle(cornerRadius: 10).stroke(
                        copiedClipId == clip.id ? RheaTheme.green.opacity(0.4) : .white.opacity(0.04), lineWidth: 1))
            )
        }
        .buttonStyle(.plain)
        .contextMenu {
            Button { Task { await togglePin(clip) } } label: {
                Label(clip.pinned ? "Unpin" : "Pin", systemImage: clip.pinned ? "pin.slash" : "pin")
            }
            Button(role: .destructive) { Task { await deleteClip(clip.id) } } label: {
                Label("Delete", systemImage: "trash")
            }
        }
        .swipeActions(edge: .trailing) {
            Button(role: .destructive) { Task { await deleteClip(clip.id) } } label: {
                Label("Delete", systemImage: "trash")
            }
        }
    }

    private var clearButton: some View {
        Button { Task { await clearAll() } } label: {
            HStack(spacing: 6) {
                Image(systemName: "trash").font(.system(size: 11))
                Text("Clear History").font(.system(size: 11, weight: .medium, design: .monospaced))
            }
            .foregroundStyle(RheaTheme.red)
            .frame(maxWidth: .infinity).padding(.vertical, 10)
            .background(
                RoundedRectangle(cornerRadius: 12).fill(RheaTheme.red.opacity(0.08))
                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(RheaTheme.red.opacity(0.2), lineWidth: 1))
            )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Helpers
    private func sectionHeader(_ title: String, icon: String) -> some View {
        HStack(spacing: 6) {
            Image(systemName: icon).font(.system(size: 11)).foregroundStyle(RheaTheme.accent)
            Text(title).font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(RheaTheme.accent.opacity(0.8))
            Spacer()
        }
    }

    private func typeIcon(_ type: String) -> String {
        switch type {
        case "url": return "\u{1F517}"; case "code": return "\u{1F4BB}"
        case "image": return "\u{1F5BC}"; default: return "\u{1F4CB}"
        }
    }

    @ViewBuilder
    private func privacyBadge(_ clip: ClipEntry) -> some View {
        switch clip.privacy {
        case "sensitive": Text("\u{1F512}").font(.system(size: 10))
        case "secret": Text("\u{1F510}").font(.system(size: 10))
        default: EmptyView()
        }
    }

    private func relativeTime(_ iso: String) -> String {
        let fmt = ISO8601DateFormatter()
        fmt.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let date = fmt.date(from: iso) ?? ISO8601DateFormatter().date(from: iso) ?? Date.distantPast
        let s = Int(Date().timeIntervalSince(date))
        if s < 60 { return "now" }; if s < 3600 { return "\(s / 60)m ago" }
        if s < 86400 { return "\(s / 3600)h ago" }; if s < 172800 { return "yesterday" }
        return "\(s / 86400)d ago"
    }

    private var currentDeviceName: String {
        #if os(iOS)
        return UIDevice.current.name
        #elseif os(macOS)
        return Host.current().localizedName ?? "Mac"
        #else
        return "Unknown"
        #endif
    }

    private var localClipboardContent: String? {
        #if os(iOS)
        return UIPasteboard.general.string
        #elseif os(macOS)
        return NSPasteboard.general.string(forType: .string)
        #else
        return nil
        #endif
    }

    private func copyToLocal(_ clip: ClipEntry) {
        guard clip.privacy != "secret" else { return }
        #if os(iOS)
        UIPasteboard.general.string = clip.content
        #elseif os(macOS)
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(clip.content, forType: .string)
        #endif
        copiedClipId = clip.id
        withAnimation(.easeInOut(duration: 0.25)) { showCopiedToast = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            withAnimation(.easeInOut(duration: 0.25)) { showCopiedToast = false; copiedClipId = nil }
        }
    }

    // MARK: - Auth
    private func authedRequest(_ url: URL, method: String = "GET") -> URLRequest {
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token = AuthManager.shared.token {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        } else {
            req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        }
        return req
    }

    // MARK: - Networking
    private func fetchClips() async {
        guard let url = URL(string: "\(apiBaseURL)/clipboard") else { return }
        do {
            let (data, response) = try await URLSession.shared.data(for: authedRequest(url))
            if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                let resp = try JSONDecoder().decode(ClipListResponse.self, from: data)
                await MainActor.run { connected = true; clips = resp.clips; isLoading = false }
            } else {
                await MainActor.run { connected = false; isLoading = false }
            }
        } catch {
            await MainActor.run { connected = false; isLoading = false; errorText = error.localizedDescription }
        }
    }

    private func pushClipboard(_ text: String) async {
        guard let url = URL(string: "\(apiBaseURL)/clipboard") else { return }
        isPushing = true
        var req = authedRequest(url, method: "POST")
        req.httpBody = try? JSONEncoder().encode([
            "content": text,
            "content_type": text.hasPrefix("http") ? "url" : "text",
            "device_name": currentDeviceName
        ])
        do {
            let (_, resp) = try await URLSession.shared.data(for: req)
            if let http = resp as? HTTPURLResponse, http.statusCode < 300 { await fetchClips() }
        } catch {}
        await MainActor.run { isPushing = false }
    }

    private func deleteClip(_ id: String) async {
        guard let url = URL(string: "\(apiBaseURL)/clipboard/\(id)") else { return }
        do {
            _ = try await URLSession.shared.data(for: authedRequest(url, method: "DELETE"))
            await MainActor.run { clips.removeAll { $0.id == id } }
        } catch {}
    }

    private func togglePin(_ clip: ClipEntry) async {
        let action = clip.pinned ? "unpin" : "pin"
        guard let url = URL(string: "\(apiBaseURL)/clipboard/\(clip.id)/\(action)") else { return }
        do {
            _ = try await URLSession.shared.data(for: authedRequest(url, method: "POST"))
            await fetchClips()
        } catch {}
    }

    private func clearAll() async {
        guard let url = URL(string: "\(apiBaseURL)/clipboard") else { return }
        do {
            _ = try await URLSession.shared.data(for: authedRequest(url, method: "DELETE"))
            await MainActor.run { clips = [] }
        } catch {}
    }

    private func startPolling() {
        pollTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
            Task { await fetchClips() }
        }
    }

    private func stopPolling() { pollTimer?.invalidate(); pollTimer = nil }
}
