import Foundation
import Combine
import os.log

#if canImport(TailscaleKit)
import TailscaleKit
#endif

/// Rhea Mesh Manager — agent-to-agent networking via Tailscale/Headscale.
///
/// Uses TailscaleKit (BSD-3-Clause) to create a userspace mesh node.
/// Each device gets a stable IP on the rhea.mesh tailnet.
/// No Tailscale account needed — connects to self-hosted Headscale.
///
/// Architecture:
///   App → MeshManager → TailscaleKit → Headscale (control) → DERP/Direct → Peer
///
/// Usage:
///   @StateObject var mesh = MeshManager.shared
///   Button("Connect") { Task { try await mesh.connect() } }
///   Text(mesh.statusText)
public class MeshManager: ObservableObject {
    public static let shared = MeshManager()

    @Published public var isConnected = false
    @Published public var meshIP: String?
    @Published public var meshIPv6: String?
    @Published public var peers: [MeshPeer] = []
    @Published public var statusText = "Disconnected"

    private let log = Logger(subsystem: "com.rhea.preview", category: "mesh")
    #if canImport(TailscaleKit)
    private var tsNode: TailscaleNode?
    #endif
    private var node: AnyObject?  // Stub fallback when TailscaleKit is not linked
    private let queue = DispatchQueue(label: "com.rhea.mesh", qos: .userInitiated)

    // Mesh configuration — points to self-hosted Headscale
    public struct MeshConfig {
        public let controlURL: String
        public let authKey: String?
        public let hostname: String
        public let ephemeral: Bool

        public init(
            controlURL: String = "https://headscale.timelabs.ru",
            authKey: String? = nil,
            hostname: String = "rhea-ios",
            ephemeral: Bool = false
        ) {
            self.controlURL = controlURL
            self.authKey = authKey
            self.hostname = hostname
            self.ephemeral = ephemeral
        }
    }

    private var config: MeshConfig?

    private init() {}

    // MARK: - Public API

    /// Connect to the Rhea mesh network.
    /// Uses TailscaleKit to establish a userspace node that registers with Headscale.
    public func connect(config: MeshConfig = MeshConfig()) async throws {
        self.config = config
        log.info("Connecting to mesh: \(config.controlURL)")

        await MainActor.run {
            statusText = "Connecting..."
        }

        // Dynamically load TailscaleKit if available
        // This allows the app to compile without TailscaleKit linked,
        // with mesh features disabled gracefully.
        guard let tailscaleKitAvailable = isTailscaleKitAvailable() else {
            log.warning("TailscaleKit not available — mesh disabled")
            await MainActor.run {
                statusText = "Mesh unavailable"
            }
            return
        }

        // Create state directory in app group container
        let statePath = meshStatePath()

        do {
            let node = try await createTailscaleNode(
                hostname: config.hostname,
                path: statePath,
                authKey: config.authKey,
                controlURL: config.controlURL,
                ephemeral: config.ephemeral
            )
            self.node = node

            // Bring the node up
            try await bringNodeUp(node)

            // Get assigned IPs
            let ips = try await getNodeIPs(node)

            await MainActor.run {
                self.meshIP = ips.ipv4
                self.meshIPv6 = ips.ipv6
                self.isConnected = true
                self.statusText = "Connected: \(ips.ipv4 ?? "...")"
            }

            log.info("Mesh connected: \(ips.ipv4 ?? "no-ip")")
        } catch {
            log.error("Mesh connection failed: \(error.localizedDescription)")
            await MainActor.run {
                statusText = "Failed: \(error.localizedDescription)"
                isConnected = false
            }
            throw error
        }
    }

    /// Disconnect from the mesh.
    public func disconnect() async {
        #if canImport(TailscaleKit)
        let hasNode = tsNode != nil || node != nil
        #else
        let hasNode = node != nil
        #endif
        guard hasNode else { return }
        log.info("Disconnecting from mesh...")

        await closeNode(node ?? NSObject())
        self.node = nil

        await MainActor.run {
            isConnected = false
            meshIP = nil
            meshIPv6 = nil
            peers = []
            statusText = "Disconnected"
        }
    }

    /// Send data to a peer on the mesh.
    public func send(to peerIP: String, port: UInt16, data: Data) async throws {
        guard let node else { throw MeshError.notConnected }
        try await dialAndSend(node: node, address: "\(peerIP):\(port)", data: data)
    }

    /// Make an HTTP request to a peer on the mesh via the tailnet.
    public func request(url: URL) async throws -> (Data, URLResponse) {
        guard let node else { throw MeshError.notConnected }
        return try await tailscaleHTTPRequest(node: node, url: url)
    }

    // MARK: - TailscaleKit Bridge

    // Uses #if canImport(TailscaleKit) for compile-time integration.
    // When TailscaleKit.xcframework is linked (via project.yml), real mesh networking is active.
    // When not linked, falls back to MeshNodeStub for UI testing.

    private func isTailscaleKitAvailable() -> Bool? {
        #if canImport(TailscaleKit)
        return true
        #else
        return NSClassFromString("TailscaleKit.TailscaleNode") != nil ? true : nil
        #endif
    }

    private func createTailscaleNode(
        hostname: String,
        path: String,
        authKey: String?,
        controlURL: String,
        ephemeral: Bool
    ) async throws -> AnyObject {
        #if canImport(TailscaleKit)
        let config = Configuration(
            hostName: hostname,
            path: path,
            authKey: authKey,
            controlURL: controlURL,
            ephemeral: ephemeral
        )
        let tsNode = try TailscaleNode(config: config, logger: nil)
        self.tsNode = tsNode
        log.info("Created TailscaleKit node: \(hostname) → \(controlURL)")
        return tsNode as AnyObject
        #else
        // Stub fallback when TailscaleKit.xcframework is not linked
        log.info("Creating stub mesh node: \(hostname) → \(controlURL)")
        return MeshNodeStub(hostname: hostname, controlURL: controlURL, authKey: authKey) as AnyObject
        #endif
    }

    private func bringNodeUp(_ node: AnyObject) async throws {
        #if canImport(TailscaleKit)
        if let tsNode {
            try await tsNode.up()
            return
        }
        #endif
        if let stub = node as? MeshNodeStub {
            try await stub.up()
            return
        }
    }

    private func getNodeIPs(_ node: AnyObject) async throws -> (ipv4: String?, ipv6: String?) {
        #if canImport(TailscaleKit)
        if let tsNode {
            let addrs = try await tsNode.addrs()
            return (ipv4: addrs.ip4, ipv6: addrs.ip6)
        }
        #endif
        if let stub = node as? MeshNodeStub {
            return stub.ips
        }
        return (nil, nil)
    }

    private func closeNode(_ node: AnyObject) async {
        #if canImport(TailscaleKit)
        if let tsNode {
            try? await tsNode.close()
            self.tsNode = nil
            return
        }
        #endif
        if let stub = node as? MeshNodeStub {
            await stub.close()
            return
        }
    }

    private func dialAndSend(node: AnyObject, address: String, data: Data) async throws {
        log.info("Mesh send to \(address): \(data.count) bytes")
        #if canImport(TailscaleKit)
        if let tsNode, let handle = await tsNode.tailscale {
            let conn = try await OutgoingConnection(
                tailscale: handle,
                to: address,
                proto: .tcp,
                logger: BlackholeLogger()
            )
            try await conn.connect()
            try await conn.send(data)
            await conn.close()
            return
        }
        #endif
        // Stub: log only
    }

    private func tailscaleHTTPRequest(node: AnyObject, url: URL) async throws -> (Data, URLResponse) {
        log.info("Mesh HTTP: \(url)")
        #if canImport(TailscaleKit)
        if let tsNode {
            let (sessionConfig, _) = try await URLSessionConfiguration.tailscaleSession(tsNode)
            let session = URLSession(configuration: sessionConfig)
            return try await session.data(from: url)
        }
        #endif
        // Fallback: regular URLSession (no tailnet routing)
        return try await URLSession.shared.data(from: url)
    }

    private func meshStatePath() -> String {
        if let container = FileManager.default.containerURL(
            forSecurityApplicationGroupIdentifier: "group.com.rhea.preview"
        ) {
            let meshDir = container.appendingPathComponent("mesh", isDirectory: true)
            try? FileManager.default.createDirectory(at: meshDir, withIntermediateDirectories: true)
            return meshDir.path
        }
        // Fallback to documents
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let meshDir = docs.appendingPathComponent("mesh", isDirectory: true)
        try? FileManager.default.createDirectory(at: meshDir, withIntermediateDirectories: true)
        return meshDir.path
    }

    // MARK: - Types

    public struct MeshPeer: Identifiable {
        public let id: String
        public let name: String
        public let ip: String
        public let isOnline: Bool
        public let lastSeen: Date?
    }

    public enum MeshError: Error, LocalizedError {
        case notConnected
        case frameworkMissing

        public var errorDescription: String? {
            switch self {
            case .notConnected: return "Not connected to mesh"
            case .frameworkMissing: return "TailscaleKit not available"
            }
        }
    }
}

// MARK: - Mesh Node Stub (replaced by TailscaleKit when linked)

/// Simulates a mesh node when TailscaleKit.xcframework is not linked.
/// Allows the app to compile, show UI, and test the flow without the Go binary.
private class MeshNodeStub {
    let hostname: String
    let controlURL: String
    let authKey: String?
    var ips: (ipv4: String?, ipv6: String?) = (nil, nil)

    init(hostname: String, controlURL: String, authKey: String?) {
        self.hostname = hostname
        self.controlURL = controlURL
        self.authKey = authKey
    }

    func up() async throws {
        // Simulate connection delay
        try await Task.sleep(nanoseconds: 500_000_000)
        // Assign simulated tailnet IP
        ips = ("100.64.0.\(Int.random(in: 2...254))", "fd7a:115c:a1e0::1")
    }

    func close() async {
        ips = (nil, nil)
    }
}
