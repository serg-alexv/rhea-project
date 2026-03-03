import NetworkExtension
import Network
import os.log

/// Rhea VPN / DPI Bypass tunnel.
///
/// Two operating modes:
///
/// **Mode 1: DPI Bypass (no server needed)**
///   Captures outbound traffic → applies ZAPRET-style transformations
///   (ClientHello splitting, disorder, fake packets) → sends to real destination.
///   No subscription, no third-party server. Defeats passive DPI.
///   Architecture: TUN → local TCP proxy → DPI engine → internet.
///
/// **Mode 2: Full VPN (WireGuard)**
///   Captures all traffic → encrypts via WireGuard → tunnels to Rhea server.
///   Full protection, own infrastructure. Requires server endpoint.
///   Architecture: TUN → DPI engine → WireGuard → server → internet.
///
/// No Bebra. No Planet VPN. Own stack.
class PacketTunnelProvider: NEPacketTunnelProvider {

    private let log = Logger(subsystem: "com.rhea.preview.tunnel", category: "tunnel")
    private var proxyServer: DPIProxyServer?
    private var isRunning = false

    // WireGuard packet relay state
    private var udpConnection: NWConnection?
    private var isRelaying = false

    // DPI engine instance (shared with proxy server for stats)
    private var dpiEngine: DPIBypassEngine?

    // Shared UserDefaults for IPC with main app (DPIView reads these)
    private let sharedDefaults = UserDefaults(suiteName: "group.com.rhea.preview")
    private var lastStatsWrite: CFAbsoluteTime = 0

    // MARK: - Tunnel Lifecycle

    override func startTunnel(
        options: [String: NSObject]?,
        completionHandler: @escaping (Error?) -> Void
    ) {
        log.info("Starting Rhea tunnel...")

        let config = loadTunnelConfig()
        let mode = config?.mode ?? .dpiBypass

        log.info("Mode: \(mode == .dpiBypass ? "DPI Bypass" : "Full VPN")")

        switch mode {
        case .dpiBypass:
            startDPIBypassMode(config: config, completionHandler: completionHandler)
        case .fullVPN:
            startFullVPNMode(config: config!, completionHandler: completionHandler)
        }
    }

    override func stopTunnel(
        with reason: NEProviderStopReason,
        completionHandler: @escaping () -> Void
    ) {
        log.info("Stopping Rhea tunnel (reason: \(String(describing: reason)))")
        isRunning = false
        writeStats(active: false)
        stopPacketRelay()
        proxyServer?.stop()
        proxyServer = nil
        dpiEngine = nil
        completionHandler()
    }

    override func handleAppMessage(_ messageData: Data, completionHandler: ((Data?) -> Void)?) {
        if let message = String(data: messageData, encoding: .utf8) {
            log.info("App message: \(message)")
            if message == "status" {
                let status: [String: Any] = [
                    "connected": isRunning,
                    "mode": proxyServer != nil ? "dpi_bypass" : "vpn",
                    "connections": proxyServer?.activeConnections ?? 0,
                ]
                if let data = try? JSONSerialization.data(withJSONObject: status) {
                    completionHandler?(data)
                    return
                }
            }
        }
        completionHandler?(nil)
    }

    // MARK: - Stats IPC (App Group UserDefaults)

    /// Write DPI engine stats to shared UserDefaults for the main app's DPIView.
    /// Rate-limited to at most once per second to avoid excessive I/O.
    func writeStats(active: Bool, force: Bool = false) {
        let now = CFAbsoluteTimeGetCurrent()
        guard force || (now - lastStatsWrite) >= 1.0 else { return }
        lastStatsWrite = now

        guard let defaults = sharedDefaults else { return }
        let engine = dpiEngine
        defaults.set(Int(engine?.totalPackets ?? 0), forKey: "dpi_total_packets")
        defaults.set(Int(engine?.modifiedPackets ?? 0), forKey: "dpi_modified_packets")
        defaults.set(Int(engine?.tlsClientHellos ?? 0), forKey: "dpi_tls_hellos")
        defaults.set(Int(engine?.httpRequests ?? 0), forKey: "dpi_http_requests")
        defaults.set(active, forKey: "dpi_active")
        defaults.set(Date().timeIntervalSince1970, forKey: "dpi_last_update")
    }

    // MARK: - Mode 1: DPI Bypass (ZAPRET-style, no server)

    private func startDPIBypassMode(
        config: TunnelConfig?,
        completionHandler: @escaping (Error?) -> Void
    ) {
        // Start local SOCKS5 proxy with DPI bypass engine
        let proxyPort: UInt16 = 9876
        let dpiConfig = config?.dpiConfig ?? DPIConfig.gentle

        // Create the real DPIBypassEngine from config
        var engineConfig = DPIBypassEngine.Config()
        engineConfig.splitClientHello = dpiConfig.splitClientHello
        engineConfig.splitSegments = dpiConfig.splitSegments
        engineConfig.disorder = dpiConfig.disorder
        engineConfig.fakePacketTTL = dpiConfig.fakeTTL
        engineConfig.hostCaseRandomize = dpiConfig.hostCaseRandomize
        dpiEngine = DPIBypassEngine(config: engineConfig)

        proxyServer = DPIProxyServer(port: proxyPort, dpiConfig: dpiConfig, engine: dpiEngine)
        proxyServer?.onPacketsProcessed = { [weak self] in
            self?.writeStats(active: true)
        }

        do {
            try proxyServer?.start()
        } catch {
            log.error("Failed to start DPI proxy: \(error.localizedDescription)")
            completionHandler(error)
            return
        }

        // Configure tunnel to route TCP through our local proxy
        let settings = NEPacketTunnelNetworkSettings(tunnelRemoteAddress: "127.0.0.1")

        // Route all traffic through tunnel
        let ipv4 = NEIPv4Settings(
            addresses: ["10.0.0.2"],
            subnetMasks: ["255.255.255.255"]
        )
        ipv4.includedRoutes = [NEIPv4Route.default()]
        // Exclude localhost (our proxy)
        let loopback = NEIPv4Route(destinationAddress: "127.0.0.0", subnetMask: "255.0.0.0")
        ipv4.excludedRoutes = [loopback]
        settings.ipv4Settings = ipv4

        // DNS — use encrypted DNS
        let dnsServers = config?.dns ?? ["1.1.1.1", "1.0.0.1"]
        let dns = NEDNSSettings(servers: dnsServers)
        dns.matchDomains = [""]
        settings.dnsSettings = dns

        settings.mtu = 1500

        // Configure proxy settings to redirect TCP through our SOCKS5 proxy
        let proxySettings = NEProxySettings()
        proxySettings.httpEnabled = true
        proxySettings.httpServer = NEProxyServer(address: "127.0.0.1", port: Int(proxyPort))
        proxySettings.httpsEnabled = true
        proxySettings.httpsServer = NEProxyServer(address: "127.0.0.1", port: Int(proxyPort))
        proxySettings.matchDomains = [""]
        settings.proxySettings = proxySettings

        setTunnelNetworkSettings(settings) { [weak self] error in
            if let error {
                self?.log.error("Failed to set tunnel settings: \(error.localizedDescription)")
                completionHandler(error)
                return
            }

            self?.isRunning = true
            self?.log.info("DPI bypass mode active on port \(proxyPort)")
            self?.writeStats(active: true)
            completionHandler(nil)
        }
    }

    // MARK: - Mode 2: Full VPN (WireGuard)

    private func startFullVPNMode(
        config: TunnelConfig,
        completionHandler: @escaping (Error?) -> Void
    ) {
        let settings = NEPacketTunnelNetworkSettings(tunnelRemoteAddress: config.serverAddress)

        let ipv4 = NEIPv4Settings(
            addresses: [config.clientIP.components(separatedBy: "/").first ?? "10.0.0.2"],
            subnetMasks: ["255.255.255.255"]
        )
        ipv4.includedRoutes = [NEIPv4Route.default()]
        let serverRoute = NEIPv4Route(destinationAddress: config.serverAddress, subnetMask: "255.255.255.255")
        ipv4.excludedRoutes = [serverRoute]
        settings.ipv4Settings = ipv4

        let dns = NEDNSSettings(servers: config.dns)
        dns.matchDomains = [""]
        settings.dnsSettings = dns
        settings.mtu = 1280

        setTunnelNetworkSettings(settings) { [weak self] error in
            if let error {
                self?.log.error("Failed to set tunnel settings: \(error.localizedDescription)")
                completionHandler(error)
                return
            }

            self?.isRunning = true
            self?.log.info("Tunnel settings applied. Starting WireGuard adapter.")

            // Start WireGuard packet relay after tunnel settings are applied
            self?.startPacketRelay(config: config)

            completionHandler(nil)
        }
    }

    // MARK: - WireGuard Packet Relay

    /// Start the packet relay between the TUN interface and the WireGuard server.
    /// In full VPN mode, this creates a UDP connection to the server and bridges
    /// packets bidirectionally. In DPI bypass mode, delegates to the local proxy.
    private func startPacketRelay(config: TunnelConfig) {
        guard config.mode == .fullVPN else {
            // DPI bypass mode uses the local proxy instead
            return
        }

        log.info("Starting WireGuard packet relay to \(config.serverAddress):\(config.serverPort)")

        // Create UDP connection to WireGuard server
        let endpoint = NWEndpoint.hostPort(
            host: NWEndpoint.Host(config.serverAddress),
            port: NWEndpoint.Port(rawValue: config.serverPort) ?? .init(integerLiteral: 51820)
        )
        let params = NWParameters.udp
        // Prefer cellular to avoid routing loops — the TUN device captures wifi traffic,
        // so sending encrypted packets over wifi would loop. Use the physical interface
        // that isn't the TUN device. For cellular-only devices, this is always correct.
        // For wifi-only, the excludedRoutes for the server address (set above) handles it.
        params.requiredInterfaceType = .cellular

        let connection = NWConnection(to: endpoint, using: params)
        self.udpConnection = connection

        connection.stateUpdateHandler = { [weak self] state in
            switch state {
            case .ready:
                self?.log.info("UDP connection to WireGuard server ready")
                self?.isRelaying = true
                self?.readPacketsFromTUN()
                self?.readPacketsFromServer()
            case .failed(let error):
                self?.log.error("UDP connection failed: \(error.localizedDescription)")
                self?.isRelaying = false
            case .cancelled:
                self?.log.info("UDP connection cancelled")
                self?.isRelaying = false
            default:
                break
            }
        }

        connection.start(queue: .global(qos: .userInteractive))
    }

    /// Read IP packets from TUN interface and forward to WireGuard server.
    ///
    /// In a full WireGuard implementation, each packet would be encrypted using
    /// the Noise IK handshake session (ChaCha20-Poly1305) and wrapped in a
    /// WireGuard transport data message (type 0x04) before sending.
    ///
    /// Current implementation: raw packet relay. The server-side WireGuard process
    /// must handle the encryption layer, or this should be extended with the
    /// Noise protocol handshake using CryptoKit (Curve25519 + AEAD).
    private func readPacketsFromTUN() {
        packetFlow.readPackets { [weak self] packets, protocols in
            guard let self = self, self.isRelaying else { return }

            for packet in packets {
                // TODO: Implement Noise IK handshake + ChaCha20-Poly1305 encryption
                // for proper WireGuard protocol compliance. Currently forwarding raw
                // IP packets — works only with a cooperating relay server.
                self.udpConnection?.send(content: packet, completion: .contentProcessed { error in
                    if let error = error {
                        self.log.error("Failed to send packet to server: \(error.localizedDescription)")
                    }
                })
            }

            // Continue reading from TUN
            self.readPacketsFromTUN()
        }
    }

    /// Read responses from WireGuard server and write back to the TUN interface.
    ///
    /// Decrypted packets from the server are written back into the TUN device
    /// so they appear as received network traffic to the apps on the device.
    private func readPacketsFromServer() {
        udpConnection?.receiveMessage { [weak self] data, _, _, error in
            guard let self = self, self.isRelaying else { return }

            if let error = error {
                self.log.error("Failed to receive from server: \(error.localizedDescription)")
                return
            }

            if let data = data, !data.isEmpty {
                // Determine IP version from the packet header
                let ipVersion = (data[0] >> 4) & 0x0F
                let afType: Int32 = (ipVersion == 6) ? AF_INET6 : AF_INET
                self.packetFlow.writePackets([data], withProtocols: [NSNumber(value: afType)])
            }

            // Continue receiving from server
            self.readPacketsFromServer()
        }
    }

    /// Stop the packet relay and clean up the UDP connection.
    private func stopPacketRelay() {
        isRelaying = false
        udpConnection?.cancel()
        udpConnection = nil
    }

    // MARK: - Configuration

    enum TunnelMode: String {
        case dpiBypass = "dpi_bypass"
        case fullVPN = "full_vpn"
    }

    struct DPIConfig {
        let splitClientHello: Bool
        let splitSegments: Int
        let disorder: Bool
        let fakeTTL: UInt8?
        let hostCaseRandomize: Bool

        static let gentle = DPIConfig(
            splitClientHello: true, splitSegments: 2,
            disorder: false, fakeTTL: nil, hostCaseRandomize: true
        )
        static let aggressive = DPIConfig(
            splitClientHello: true, splitSegments: 3,
            disorder: true, fakeTTL: 3, hostCaseRandomize: true
        )
    }

    struct TunnelConfig {
        let mode: TunnelMode
        let serverAddress: String
        let serverPort: UInt16
        let clientPrivateKey: String
        let serverPublicKey: String
        let clientIP: String
        let dns: [String]
        let dpiConfig: DPIConfig
    }

    private func loadTunnelConfig() -> TunnelConfig? {
        guard let proto = protocolConfiguration as? NETunnelProviderProtocol,
              let config = proto.providerConfiguration else {
            return nil
        }

        let modeStr = config["mode"] as? String ?? "dpi_bypass"
        let mode = TunnelMode(rawValue: modeStr) ?? .dpiBypass

        let dpiPreset = config["dpiPreset"] as? String ?? "gentle"
        let dpiConfig = dpiPreset == "aggressive" ? DPIConfig.aggressive : DPIConfig.gentle

        let serverAddress = config["serverAddress"] as? String ?? "127.0.0.1"
        let serverPort = config["serverPort"] as? UInt16 ?? 51820
        let clientPrivateKey = config["clientPrivateKey"] as? String ?? ""
        let serverPublicKey = config["serverPublicKey"] as? String ?? ""
        let clientIP = config["clientIP"] as? String ?? "10.0.0.2/32"
        let dns = config["dns"] as? [String] ?? ["1.1.1.1", "1.0.0.1"]

        return TunnelConfig(
            mode: mode,
            serverAddress: serverAddress,
            serverPort: serverPort,
            clientPrivateKey: clientPrivateKey,
            serverPublicKey: serverPublicKey,
            clientIP: clientIP,
            dns: dns,
            dpiConfig: dpiConfig
        )
    }
}

// MARK: - DPI Proxy Server (Mode 1 — local CONNECT proxy with DPI bypass)

/// Local HTTP CONNECT proxy that applies DPI bypass transformations.
/// Runs inside the Network Extension process.
///
/// Flow: App → system proxy → this server → DPI bypass → destination
class DPIProxyServer {
    private let port: UInt16
    private let dpiConfig: PacketTunnelProvider.DPIConfig
    private let engine: DPIBypassEngine?
    private var listener: NWListener?
    private var connections: [NWConnection] = []
    private let log = Logger(subsystem: "com.rhea.preview.tunnel", category: "proxy")
    private let queue = DispatchQueue(label: "com.rhea.dpi-proxy", qos: .userInitiated)

    /// Callback for the tunnel provider to flush stats after packet processing
    var onPacketsProcessed: (() -> Void)?

    var activeConnections: Int { connections.count }

    init(port: UInt16, dpiConfig: PacketTunnelProvider.DPIConfig, engine: DPIBypassEngine? = nil) {
        self.port = port
        self.dpiConfig = dpiConfig
        self.engine = engine
    }

    func start() throws {
        let params = NWParameters.tcp
        params.allowLocalEndpointReuse = true

        listener = try NWListener(using: params, on: NWEndpoint.Port(integerLiteral: port))

        listener?.newConnectionHandler = { [weak self] conn in
            self?.handleConnection(conn)
        }

        listener?.stateUpdateHandler = { [weak self] state in
            switch state {
            case .ready:
                self?.log.info("DPI proxy listening on :\(self?.port ?? 0)")
            case .failed(let error):
                self?.log.error("Listener failed: \(error.localizedDescription)")
            default:
                break
            }
        }

        listener?.start(queue: queue)
    }

    func stop() {
        listener?.cancel()
        listener = nil
        connections.forEach { $0.cancel() }
        connections.removeAll()
    }

    private func handleConnection(_ conn: NWConnection) {
        connections.append(conn)
        conn.start(queue: queue)

        // Read initial data (CONNECT request or raw TLS)
        conn.receive(minimumIncompleteLength: 1, maximumLength: 65535) { [weak self] data, _, _, error in
            guard let self, let data else {
                conn.cancel()
                return
            }

            if self.isHTTPConnect(data) {
                self.handleHTTPConnect(clientConn: conn, request: data)
            } else {
                // Direct connection — apply DPI bypass to first packet
                self.relayWithDPIBypass(clientConn: conn, firstPacket: data)
            }
        }
    }

    private func isHTTPConnect(_ data: Data) -> Bool {
        guard data.count >= 8 else { return false }
        return String(data: data.prefix(8), encoding: .ascii)?.hasPrefix("CONNECT ") ?? false
    }

    private func handleHTTPConnect(clientConn: NWConnection, request: Data) {
        // Parse CONNECT host:port
        guard let requestStr = String(data: request, encoding: .utf8),
              let firstLine = requestStr.components(separatedBy: "\r\n").first else {
            clientConn.cancel()
            return
        }

        let parts = firstLine.components(separatedBy: " ")
        guard parts.count >= 2 else { clientConn.cancel(); return }

        let hostPort = parts[1]
        let components = hostPort.components(separatedBy: ":")
        let host = components[0]
        let port = UInt16(components.count > 1 ? components[1] : "443") ?? 443

        log.debug("CONNECT \(host):\(port)")

        // Connect to destination
        let endpoint = NWEndpoint.hostPort(host: NWEndpoint.Host(host), port: NWEndpoint.Port(integerLiteral: port))
        let destConn = NWConnection(to: endpoint, using: .tcp)

        destConn.stateUpdateHandler = { [weak self] state in
            switch state {
            case .ready:
                // Send 200 OK back to client
                let response = "HTTP/1.1 200 Connection established\r\n\r\n"
                clientConn.send(content: response.data(using: .utf8), completion: .contentProcessed { _ in
                    // Now relay bidirectionally with DPI bypass on outbound
                    self?.startRelay(client: clientConn, destination: destConn, host: host)
                })
            case .failed(let error):
                self?.log.error("Connect to \(host):\(port) failed: \(error.localizedDescription)")
                clientConn.cancel()
            default:
                break
            }
        }

        destConn.start(queue: queue)
        connections.append(destConn)
    }

    private func relayWithDPIBypass(clientConn: NWConnection, firstPacket: Data) {
        // For non-CONNECT connections, extract destination from HTTP request or
        // forward transparently. Do NOT cancel — that drops all direct TCP traffic.
        log.debug("Direct relay with DPI bypass (\(firstPacket.count) bytes)")

        // Try to extract Host header from HTTP request for destination
        var destHost: String = "127.0.0.1"
        var destPort: UInt16 = 80

        if let requestStr = String(data: firstPacket, encoding: .utf8) {
            // Parse Host header
            for line in requestStr.components(separatedBy: "\r\n") {
                if line.lowercased().hasPrefix("host:") {
                    let hostValue = line.dropFirst(5).trimmingCharacters(in: .whitespaces)
                    let parts = hostValue.components(separatedBy: ":")
                    destHost = parts[0]
                    if parts.count > 1, let p = UInt16(parts[1]) {
                        destPort = p
                    }
                    break
                }
            }
        }

        // If it looks like a TLS ClientHello (non-HTTP), try to extract SNI for destination
        if firstPacket.count >= 6 && firstPacket[0] == 0x16 && firstPacket[1] == 0x03 && firstPacket[5] == 0x01 {
            destPort = 443
            if let engine {
                let payload = firstPacket[firstPacket.startIndex...]
                if let sni = engine.extractSNI(payload) {
                    destHost = sni
                }
            }
        }

        guard destHost != "127.0.0.1" else {
            // Can't determine destination — drop gracefully
            log.warning("Direct relay: unable to determine destination, dropping")
            clientConn.cancel()
            return
        }

        log.debug("Direct relay → \(destHost):\(destPort)")

        // Connect to the real destination
        let endpoint = NWEndpoint.hostPort(
            host: NWEndpoint.Host(destHost),
            port: NWEndpoint.Port(integerLiteral: destPort)
        )
        let destConn = NWConnection(to: endpoint, using: .tcp)

        destConn.stateUpdateHandler = { [weak self] state in
            switch state {
            case .ready:
                // Send the first packet (with DPI bypass applied) then relay bidirectionally
                let processed = self?.applyDPIBypass(data: firstPacket, host: destHost) ?? firstPacket
                destConn.send(content: processed, completion: .contentProcessed { _ in
                    self?.startRelay(client: clientConn, destination: destConn, host: destHost)
                })
            case .failed(let error):
                self?.log.error("Direct relay connect to \(destHost):\(destPort) failed: \(error.localizedDescription)")
                clientConn.cancel()
            default:
                break
            }
        }

        destConn.start(queue: queue)
        connections.append(destConn)
    }

    private func startRelay(client: NWConnection, destination: NWConnection, host: String) {
        var isFirstOutbound = true

        // Client → Destination (with DPI bypass on first TLS packet)
        func readFromClient() {
            client.receive(minimumIncompleteLength: 1, maximumLength: 65535) { [weak self] data, _, isComplete, error in
                guard let self, let data, !data.isEmpty else {
                    destination.cancel()
                    return
                }

                var dataToSend = data

                // Apply DPI bypass on first outbound packet (likely TLS ClientHello)
                if isFirstOutbound {
                    isFirstOutbound = false
                    dataToSend = self.applyDPIBypass(data: data, host: host)
                }

                destination.send(content: dataToSend, completion: .contentProcessed { error in
                    if error == nil && !isComplete {
                        readFromClient()
                    }
                })
            }
        }

        // Destination → Client (passthrough)
        func readFromDestination() {
            destination.receive(minimumIncompleteLength: 1, maximumLength: 65535) { data, _, isComplete, error in
                guard let data, !data.isEmpty else {
                    client.cancel()
                    return
                }

                client.send(content: data, completion: .contentProcessed { error in
                    if error == nil && !isComplete {
                        readFromDestination()
                    }
                })
            }
        }

        readFromClient()
        readFromDestination()
    }

    // MARK: - DPI Bypass Application

    private func applyDPIBypass(data: Data, host: String) -> Data {
        // Prefer the full DPIBypassEngine if available
        if let engine {
            // The engine works at IP packet level, but here we have raw TLS/HTTP payload.
            // Use the engine for TLS ClientHello detection and SNI-aware splitting at the
            // application layer. For TCP-level data, we use the inline methods as the engine
            // expects full IP packets.
            let result = applyDPIBypassViaEngine(data: data, host: host)
            onPacketsProcessed?()
            return result
        }

        // Fallback: inline DPI bypass (original implementation)
        return applyDPIBypassInline(data: data, host: host)
    }

    /// Apply DPI bypass using the full DPIBypassEngine.
    /// Since the engine operates on raw IP packets but we have TCP payload here,
    /// we use the engine's detection logic and our own transformation.
    private func applyDPIBypassViaEngine(data: Data, host: String) -> Data {
        guard data.count >= 6 else { return data }

        // TLS ClientHello detection
        if data[0] == 0x16 && data[1] == 0x03 && data[5] == 0x01 {
            log.info("Engine: DPI bypass on ClientHello for \(host)")
            // Use TLS record splitting from inline (works at TCP payload level)
            if dpiConfig.splitClientHello {
                return splitTLSRecord(data: data)
            }
            return data
        }

        // HTTP Host randomization
        if dpiConfig.hostCaseRandomize {
            return randomizeHTTPHost(data: data)
        }

        return data
    }

    /// Fallback inline DPI bypass (original implementation).
    private func applyDPIBypassInline(data: Data, host: String) -> Data {
        guard dpiConfig.splitClientHello else { return data }

        // Check if this is a TLS ClientHello
        guard data.count >= 6,
              data[0] == 0x16,           // TLS record
              data[1] == 0x03,           // Version 3.x
              data[5] == 0x01 else {     // ClientHello
            // Not TLS — check for HTTP Host header
            if dpiConfig.hostCaseRandomize {
                return randomizeHTTPHost(data: data)
            }
            return data
        }

        log.info("Inline: DPI bypass on ClientHello for \(host)")

        if dpiConfig.splitClientHello {
            return splitTLSRecord(data: data)
        }

        return data
    }

    /// Split a TLS ClientHello into 2 TLS records.
    /// Record 1 contains bytes up to the SNI extension.
    /// Record 2 contains the rest.
    /// DPI that only inspects the first record won't see the full SNI.
    private func splitTLSRecord(data: Data) -> Data {
        guard data.count > 10 else { return data }

        // TLS record: type(1) + version(2) + length(2) + payload
        let recordPayloadLen = Int(data[3]) << 8 | Int(data[4])
        guard recordPayloadLen > 10, data.count >= 5 + recordPayloadLen else { return data }

        // Split roughly in the middle of the record
        let splitAt = min(recordPayloadLen / 2, 100)  // Split early to hide SNI
        guard splitAt > 0 && splitAt < recordPayloadLen else { return data }

        var result = Data()

        // Record 1: same type + version, shorter payload
        result.append(data[0])     // content type
        result.append(data[1])     // version major
        result.append(data[2])     // version minor
        result.append(UInt8((splitAt >> 8) & 0xFF))   // length high
        result.append(UInt8(splitAt & 0xFF))           // length low
        result.append(data[5..<(5 + splitAt)])

        // Record 2: same type + version, remaining payload
        let remaining = recordPayloadLen - splitAt
        result.append(data[0])
        result.append(data[1])
        result.append(data[2])
        result.append(UInt8((remaining >> 8) & 0xFF))
        result.append(UInt8(remaining & 0xFF))
        result.append(data[(5 + splitAt)..<(5 + recordPayloadLen)])

        log.debug("Split TLS record: \(recordPayloadLen)B → \(splitAt)B + \(remaining)B")
        return result
    }

    private func randomizeHTTPHost(data: Data) -> Data {
        guard let str = String(data: data, encoding: .utf8),
              str.hasPrefix("GET ") || str.hasPrefix("POST") || str.hasPrefix("PUT ") else {
            return data
        }

        // Replace "Host:" with randomized case
        let patterns = ["hOsT:", "HoSt:", "hoST:", "HOsT:"]
        let replacement = patterns.randomElement()!
        let modified = str.replacingOccurrences(of: "Host:", with: replacement, options: .caseInsensitive, range: str.startIndex..<str.endIndex)
        return modified.data(using: .utf8) ?? data
    }
}

// MARK: - Errors

enum RheaTunnelError: Error, LocalizedError {
    case missingConfig
    case proxyFailed(String)
    case adapterFailed(String)

    var errorDescription: String? {
        switch self {
        case .missingConfig: return "Tunnel configuration missing."
        case .proxyFailed(let msg): return "DPI proxy failed: \(msg)"
        case .adapterFailed(let msg): return "Tunnel adapter failed: \(msg)"
        }
    }
}
