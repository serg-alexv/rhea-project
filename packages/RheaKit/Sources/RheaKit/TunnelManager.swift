import NetworkExtension
import Combine
import os.log

/// Controls the Rhea VPN tunnel from the main app.
///
/// Usage:
///   @StateObject var tunnel = TunnelManager.shared
///   Toggle("VPN", isOn: $tunnel.isEnabled)
///   Text(tunnel.statusText)
///
/// The manager handles:
///   - Installing/removing the VPN profile in iOS Settings
///   - Starting/stopping the tunnel
///   - Monitoring connection status
///   - Generating WireGuard keypairs (client side)
public class TunnelManager: ObservableObject {
    public static let shared = TunnelManager()

    @Published public var status: NEVPNStatus = .disconnected
    @Published public var isEnabled = false
    @Published public var bytesIn: UInt64 = 0
    @Published public var bytesOut: UInt64 = 0
    @Published public var connectedSince: Date?

    private let log = Logger(subsystem: "com.rhea.preview", category: "tunnel")
    private var manager: NETunnelProviderManager?
    private var statusObserver: Any?

    private init() {
        loadManager()
    }

    // MARK: - Public API

    public var statusText: String {
        switch status {
        case .connected: return "Connected"
        case .connecting: return "Connecting..."
        case .disconnecting: return "Disconnecting..."
        case .disconnected: return "Disconnected"
        case .reasserting: return "Reconnecting..."
        case .invalid: return "Not configured"
        @unknown default: return "Unknown"
        }
    }

    public var isConnected: Bool { status == .connected }

    /// Configure and install the VPN profile.
    /// Call this before first connect — installs the profile in Settings → VPN.
    public func install(
        serverAddress: String,
        serverPort: UInt16 = 51820,
        serverPublicKey: String,
        clientPrivateKey: String,
        clientIP: String = "10.0.0.2/32",
        dns: [String] = ["1.1.1.1", "1.0.0.1"]
    ) async throws {
        let manager = self.manager ?? NETunnelProviderManager()

        let proto = NETunnelProviderProtocol()
        proto.providerBundleIdentifier = "com.rhea.preview.tunnel"
        proto.serverAddress = serverAddress
        proto.providerConfiguration = [
            "serverAddress": serverAddress,
            "serverPort": serverPort,
            "serverPublicKey": serverPublicKey,
            "clientPrivateKey": clientPrivateKey,
            "clientIP": clientIP,
            "dns": dns,
        ]

        manager.protocolConfiguration = proto
        manager.localizedDescription = "Rhea VPN"
        manager.isEnabled = true

        try await manager.saveToPreferences()
        try await manager.loadFromPreferences()

        self.manager = manager
        observeStatus()
        log.info("VPN profile installed: \(serverAddress)")
    }

    /// Start the VPN tunnel.
    public func connect() throws {
        guard let manager else {
            throw TunnelError.notInstalled
        }
        try manager.connection.startVPNTunnel()
        log.info("VPN tunnel starting...")
    }

    /// Stop the VPN tunnel.
    public func disconnect() {
        manager?.connection.stopVPNTunnel()
        log.info("VPN tunnel stopping...")
    }

    /// Toggle connection state.
    public func toggle() throws {
        if isConnected {
            disconnect()
        } else {
            try connect()
        }
    }

    /// Remove the VPN profile entirely.
    public func uninstall() async throws {
        guard let manager else { return }
        try await manager.removeFromPreferences()
        self.manager = nil
        self.status = .invalid
        log.info("VPN profile removed")
    }

    /// Send a message to the tunnel extension.
    public func sendMessage(_ message: String) async -> Data? {
        guard let session = manager?.connection as? NETunnelProviderSession else {
            return nil
        }
        return await withCheckedContinuation { continuation in
            do {
                try session.sendProviderMessage(message.data(using: .utf8)!) { response in
                    continuation.resume(returning: response)
                }
            } catch {
                continuation.resume(returning: nil)
            }
        }
    }

    // MARK: - Private

    private func loadManager() {
        NETunnelProviderManager.loadAllFromPreferences { [weak self] managers, error in
            guard let self else { return }
            if let error {
                self.log.error("Failed to load VPN managers: \(error.localizedDescription)")
                return
            }

            // Find existing Rhea VPN profile
            self.manager = managers?.first { mgr in
                (mgr.protocolConfiguration as? NETunnelProviderProtocol)?
                    .providerBundleIdentifier == "com.rhea.preview.tunnel"
            }

            if let manager = self.manager {
                DispatchQueue.main.async {
                    self.status = manager.connection.status
                    self.isEnabled = manager.isEnabled
                }
                self.observeStatus()
                self.log.info("Loaded existing VPN profile")
            } else {
                DispatchQueue.main.async {
                    self.status = .invalid
                }
            }
        }
    }

    private func observeStatus() {
        if let old = statusObserver {
            NotificationCenter.default.removeObserver(old)
        }
        statusObserver = NotificationCenter.default.addObserver(
            forName: .NEVPNStatusDidChange,
            object: manager?.connection,
            queue: .main
        ) { [weak self] _ in
            guard let self, let manager = self.manager else { return }
            self.status = manager.connection.status
            if manager.connection.status == .connected {
                self.connectedSince = Date()
            } else if manager.connection.status == .disconnected {
                self.connectedSince = nil
            }
        }
    }

    enum TunnelError: Error, LocalizedError {
        case notInstalled

        var errorDescription: String? {
            switch self {
            case .notInstalled: return "VPN not configured. Set up in Relay settings first."
            }
        }
    }
}
