import NetworkExtension
import os.log

/// Rhea VPN tunnel — routes all device traffic through Rhea infrastructure.
///
/// Architecture:
///   1. NETunnelProviderManager configures the VPN profile in Settings
///   2. PacketTunnelProvider creates a virtual TUN interface
///   3. Packets read from TUN → encrypted → sent to Rhea tunnel server
///   4. Server decrypts → forwards to internet → returns responses
///
/// Protocol: WireGuard (open source, audited, fast).
/// Server: Fly.io WireGuard endpoint at tunnel.rhea.dev (or self-hosted).
///
/// No third-party VPN subscription. No Bebra. No Planet. Own infrastructure.
class PacketTunnelProvider: NEPacketTunnelProvider {

    private let log = Logger(subsystem: "com.rhea.preview.tunnel", category: "tunnel")

    // MARK: - Tunnel Lifecycle

    override func startTunnel(
        options: [String: NSObject]?,
        completionHandler: @escaping (Error?) -> Void
    ) {
        log.info("Starting Rhea tunnel...")

        guard let config = loadTunnelConfig() else {
            log.error("No tunnel configuration found")
            completionHandler(RheaTunnelError.missingConfig)
            return
        }

        let tunnelSettings = buildNetworkSettings(config: config)

        setTunnelNetworkSettings(tunnelSettings) { [weak self] error in
            if let error {
                self?.log.error("Failed to set tunnel settings: \(error.localizedDescription)")
                completionHandler(error)
                return
            }

            self?.log.info("Tunnel settings applied. Starting packet relay.")
            // TODO(human): Wire WireGuard adapter here
            // The adapter reads packets from self.packetFlow,
            // encrypts them, and sends them to the server endpoint.
            //
            // See: WireGuardAdapter from wireguard-apple
            // adapter = WireGuardAdapter(with: self)
            // adapter.start(tunnelConfiguration: wgConfig) { ... }
            completionHandler(nil)
        }
    }

    override func stopTunnel(
        with reason: NEProviderStopReason,
        completionHandler: @escaping () -> Void
    ) {
        log.info("Stopping Rhea tunnel (reason: \(String(describing: reason)))")
        // TODO(human): adapter.stop { completionHandler() }
        completionHandler()
    }

    override func handleAppMessage(_ messageData: Data, completionHandler: ((Data?) -> Void)?) {
        // Main app can send messages to the extension (e.g., status queries)
        if let message = String(data: messageData, encoding: .utf8) {
            log.info("App message: \(message)")
            if message == "status" {
                let status = ["connected": true, "bytesIn": 0, "bytesOut": 0] as [String: Any]
                if let data = try? JSONSerialization.data(withJSONObject: status) {
                    completionHandler?(data)
                    return
                }
            }
        }
        completionHandler?(nil)
    }

    // MARK: - Configuration

    private struct TunnelConfig {
        let serverAddress: String     // e.g. "tunnel.rhea.dev"
        let serverPort: UInt16        // e.g. 51820 (WireGuard default)
        let clientPrivateKey: String  // WireGuard key
        let serverPublicKey: String   // WireGuard key
        let clientIP: String          // e.g. "10.0.0.2/32"
        let dns: [String]            // e.g. ["1.1.1.1", "1.0.0.1"]
    }

    private func loadTunnelConfig() -> TunnelConfig? {
        // Config comes from NETunnelProviderProtocol.providerConfiguration
        guard let proto = protocolConfiguration as? NETunnelProviderProtocol,
              let config = proto.providerConfiguration else {
            return nil
        }

        guard let serverAddress = config["serverAddress"] as? String,
              let serverPort = config["serverPort"] as? UInt16,
              let clientPrivateKey = config["clientPrivateKey"] as? String,
              let serverPublicKey = config["serverPublicKey"] as? String,
              let clientIP = config["clientIP"] as? String else {
            return nil
        }

        let dns = config["dns"] as? [String] ?? ["1.1.1.1", "1.0.0.1"]

        return TunnelConfig(
            serverAddress: serverAddress,
            serverPort: serverPort,
            clientPrivateKey: clientPrivateKey,
            serverPublicKey: serverPublicKey,
            clientIP: clientIP,
            dns: dns
        )
    }

    private func buildNetworkSettings(config: TunnelConfig) -> NEPacketTunnelNetworkSettings {
        let settings = NEPacketTunnelNetworkSettings(tunnelRemoteAddress: config.serverAddress)

        // IPv4 — route all traffic through tunnel
        let ipv4 = NEIPv4Settings(
            addresses: [config.clientIP.components(separatedBy: "/").first ?? "10.0.0.2"],
            subnetMasks: ["255.255.255.255"]
        )
        ipv4.includedRoutes = [NEIPv4Route.default()]
        // Exclude the tunnel server itself from routing (prevent loop)
        let serverRoute = NEIPv4Route(destinationAddress: config.serverAddress, subnetMask: "255.255.255.255")
        ipv4.excludedRoutes = [serverRoute]
        settings.ipv4Settings = ipv4

        // DNS — use encrypted DNS via tunnel
        let dns = NEDNSSettings(servers: config.dns)
        dns.matchDomains = [""]  // Route all DNS through tunnel
        settings.dnsSettings = dns

        // MTU
        settings.mtu = 1280

        return settings
    }
}

// MARK: - Errors

enum RheaTunnelError: Error, LocalizedError {
    case missingConfig
    case adapterFailed(String)

    var errorDescription: String? {
        switch self {
        case .missingConfig: return "Tunnel configuration missing. Configure in Relay settings."
        case .adapterFailed(let msg): return "Tunnel adapter failed: \(msg)"
        }
    }
}
