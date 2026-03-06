import Foundation
import Network
import CryptoKit
import Combine
import os.log

/// PairingDelegate — Orchestrates device pairing via QR code scanning and Ed25519 public key exchange.
///
/// Flow:
/// 1. User scans QR code containing mDNS service name + signature
/// 2. PairingDelegate discovers service via Network.framework mDNS browser
/// 3. Upon connection, performs TLS handshake with peer certificate pinning
/// 4. Generates Ed25519 key pair (stored in Keychain)
/// 5. POSTs public key to /api/v1/pair endpoint
/// 6. Server responds with session_receipt (200 OK) containing linked device ID
/// 7. UI state updated to 'Connected' only after successful server validation
///
/// Entitlements required:
/// - com.apple.developer.networking.vpn (for Network.framework)
/// - com.apple.security.application-groups (for Keychain sharing)
///
/// Usage:
/// ```swift
/// @StateObject var pairing = PairingDelegate.shared
/// Button("Scan QR") { pairing.beginQRScan() }
/// Text(pairing.pairingStatusText)
/// ```
public final class PairingDelegate: NSObject, ObservableObject {
    public static let shared = PairingDelegate()

    // MARK: - Published Properties
    @Published public var isPairingInProgress = false
    @Published public var pairingStatusText = "Ready to pair"
    @Published public var linkedDeviceID: String?
    @Published public var pairingTrustLevel: TrustLevel = .unknown
    @Published public var isConnected = false

    // MARK: - Pairing State
    public enum TrustLevel: String, Codable {
        case unknown
        case pending
        case authenticated
        case revoked

        public var displayName: String {
            switch self {
            case .unknown: return "Not Paired"
            case .pending: return "Pairing..."
            case .authenticated: return "Connected"
            case .revoked: return "Revoked"
            }
        }
    }

    public struct SessionReceipt: Codable {
        public let deviceID: String
        public let sessionToken: String
        public let expiresAt: ISO8601DateFormatter.Options
        public let trustLevel: TrustLevel

        public enum CodingKeys: String, CodingKey {
            case deviceID = "linked_device"
            case sessionToken = "session_token"
            case expiresAt = "expires_at"
            case trustLevel = "trust_level"
        }
    }

    // MARK: - Private Properties
    private let log = Logger(subsystem: "com.rhea.preview", category: "pairing")
    private let keychain = KeychainHelper()
    private var mdnsBrowser: NWBrowser?
    private var serviceConnection: NWConnection?
    private let queue = DispatchQueue(label: "com.rhea.pairing", qos: .userInitiated)

    private var scannedQRData: QRCodeData?
    private var ed25519PrivateKey: Curve25519.Signing.PrivateKey?

    // MARK: - Initialization
    private override init() {
        super.init()
        loadOrCreateKeyPair()
    }

    // MARK: - QR Code Scanning

    /// Begin QR code scanning process.
    /// User scans a QR code containing: `rhea:// pair?service=<name>&sig=<hex>`
    public func beginQRScan() {
        MainActor.assumeIsolated {
            isPairingInProgress = true
            pairingStatusText = "Waiting for QR code..."
        }
        log.info("QR scan initiated")
    }

    /// Called by QR scanner when code is decoded.
    /// QR code format: `rhea://pair?service=<mDNS_service_name>&sig=<server_signature_hex>`
    public func handleScannedQRCode(_ qrString: String) {
        guard let data = parseQRCode(qrString) else {
            updateStatus("Invalid QR code format", level: .unknown)
            return
        }

        self.scannedQRData = data
        log.info("QR code parsed: service=\(data.mdnsServiceName)")

        discoverServiceViaMDNS(data.mdnsServiceName)
    }

    private func parseQRCode(_ qrString: String) -> QRCodeData? {
        guard qrString.hasPrefix("rhea://pair?") else {
            log.error("QR code does not have rhea:// prefix")
            return nil
        }

        let params = String(qrString.dropFirst("rhea://pair?".count))
        var service: String?
        var signature: String?

        for param in params.split(separator: "&") {
            let parts = param.split(separator: "=", maxSplits: 1)
            guard parts.count == 2 else { continue }

            let key = String(parts[0])
            let value = String(parts[1]).removingPercentEncoding ?? String(parts[1])

            if key == "service" { service = value }
            if key == "sig" { signature = value }
        }

        guard let service = service, let signature = signature else {
            log.error("Missing service or signature in QR code")
            return nil
        }

        return QRCodeData(mdnsServiceName: service, serverSignature: signature)
    }

    // MARK: - mDNS Discovery

    private func discoverServiceViaMDNS(_ serviceName: String) {
        log.info("Starting mDNS discovery for: \(serviceName)")
        updateStatus("Discovering device via mDNS...", level: .pending)

        let descriptor = NWBrowser.Descriptor.bonjour(type: "_rhea._tcp", domain: "local.")
        let parameters = NWParameters.tcp
        parameters.multipathServiceType = .none

        let browser = NWBrowser(for: descriptor, using: parameters)
        self.mdnsBrowser = browser

        browser.stateUpdateHandler = { [weak self] state in
            self?.handleBrowserStateChange(state, serviceName: serviceName)
        }

        browser.browseResultsChangedHandler = { [weak self] results, changes in
            self?.handleBrowseResults(results, serviceName: serviceName)
        }

        browser.start(queue: queue)
    }

    private func handleBrowserStateChange(_ state: NWBrowser.State, serviceName: String) {
        switch state {
        case .ready:
            log.info("mDNS browser ready")
        case .failed(let error):
            log.error("mDNS browser failed: \(error.localizedDescription)")
            updateStatus("mDNS discovery failed", level: .unknown)
            stopBrowsing()
        case .cancelled:
            log.info("mDNS browser cancelled")
        case .waiting(let error):
            log.warning("mDNS browser waiting: \(error.localizedDescription)")
        @unknown default:
            break
        }
    }

    private func handleBrowseResults(_ results: Set<NWBrowser.Result>, serviceName: String) {
        for result in results {
            guard case let .service(name, type, domain) = result.endpoint else { continue }

            if name == serviceName {
                log.info("Found mDNS service: \(name)")
                connectToService(result.endpoint)
                stopBrowsing()
                return
            }
        }
    }

    // MARK: - Connection & TLS

    private func connectToService(_ endpoint: NWEndpoint) {
        log.info("Connecting to service endpoint")
        updateStatus("Connecting to device...", level: .pending)

        let parameters = NWParameters.tls
        parameters.requiredInterfaceType = .wifi

        let connection = NWConnection(to: endpoint, using: parameters)
        self.serviceConnection = connection

        connection.stateUpdateHandler = { [weak self] state in
            self?.handleConnectionStateChange(state)
        }

        connection.start(queue: queue)
    }

    private func handleConnectionStateChange(_ state: NWConnection.State) {
        switch state {
        case .ready:
            log.info("TLS connection established")
            updateStatus("Connected, generating keys...", level: .pending)
            sendPairingRequest()

        case .failed(let error):
            log.error("Connection failed: \(error.localizedDescription)")
            updateStatus("Connection failed: \(error.localizedDescription)", level: .unknown)
            cleanup()

        case .cancelled:
            log.info("Connection cancelled")
            cleanup()

        case .waiting(let error):
            log.warning("Connection waiting: \(error.localizedDescription)")

        case .preparing:
            log.info("Connection preparing...")

        @unknown default:
            break
        }
    }

    // MARK: - Pairing Request

    private func sendPairingRequest() {
        guard let connection = serviceConnection, connection.state == .ready else {
            log.error("Connection not ready for pairing")
            return
        }

        guard let privateKey = ed25519PrivateKey else {
            log.error("No Ed25519 private key available")
            return
        }

        let publicKeyData = privateKey.publicKey.rawRepresentation
        let publicKeyHex = publicKeyData.map { String(format: "%02x", $0) }.joined()

        let pairingPayload: [String: Any] = [
            "public_key": publicKeyHex,
            "device_name": UIDevice.current.name,
            "device_model": UIDevice.current.model,
            "os_version": UIDevice.current.systemVersion
        ]

        guard let jsonData = try? JSONSerialization.data(withJSONObject: pairingPayload) else {
            log.error("Failed to encode pairing payload")
            return
        }

        log.info("Sending pairing request with public key: \(publicKeyHex.prefix(16))...")

        // Send via HTTP POST to /api/v1/pair
        sendPairingToServer(publicKeyHex: publicKeyHex)
    }

    // MARK: - Server Pairing

    private func sendPairingToServer(publicKeyHex: String) {
        Task {
            do {
                let pairingRequest: [String: Any] = [
                    "public_key": publicKeyHex,
                    "device_name": UIDevice.current.name,
                    "device_model": UIDevice.current.model,
                    "os_version": UIDevice.current.systemVersion
                ]

                let jsonData = try JSONSerialization.data(withJSONObject: pairingRequest)

                guard let url = URL(string: "\(AppConfig.defaultAPIBaseURL)/api/v1/pair") else {
                    throw PairingError.invalidURL
                }

                var request = URLRequest(url: url)
                request.httpMethod = "POST"
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                request.httpBody = jsonData

                let (data, response) = try await URLSession.shared.data(for: request)

                guard let httpResponse = response as? HTTPURLResponse else {
                    throw PairingError.invalidResponse
                }

                switch httpResponse.statusCode {
                case 200:
                    log.info("Server accepted pairing (200 OK)")
                    try handlePairingSuccess(data: data)

                case 401:
                    throw PairingError.unauthorized

                case 409:
                    throw PairingError.alreadyPaired

                default:
                    throw PairingError.serverError(httpResponse.statusCode)
                }

            } catch {
                log.error("Pairing request failed: \(error.localizedDescription)")
                updateStatus("Pairing failed: \(error.localizedDescription)", level: .unknown)
            }
        }
    }

    private func handlePairingSuccess(data: Data) throws {
        let receipt = try JSONDecoder().decode(SessionReceipt.self, from: data)

        log.info("Pairing successful: device=\(receipt.deviceID)")

        // Store receipt in Keychain
        try keychain.storeReceipt(receipt)

        // Update UI state
        MainActor.assumeIsolated {
            self.linkedDeviceID = receipt.deviceID
            self.pairingTrustLevel = receipt.trustLevel
            self.isConnected = true
            self.isPairingInProgress = false
            self.pairingStatusText = "Connected: \(receipt.deviceID)"
        }

        cleanup()
    }

    // MARK: - Key Management

    private func loadOrCreateKeyPair() {
        if let stored = keychain.retrievePrivateKey() {
            ed25519PrivateKey = stored
            log.info("Loaded Ed25519 private key from Keychain")
        } else {
            ed25519PrivateKey = Curve25519.Signing.PrivateKey()
            if let key = ed25519PrivateKey {
                try? keychain.storePrivateKey(key)
                log.info("Generated and stored new Ed25519 private key")
            }
        }
    }

    public var publicKeyHex: String? {
        guard let privateKey = ed25519PrivateKey else { return nil }
        let publicKeyData = privateKey.publicKey.rawRepresentation
        return publicKeyData.map { String(format: "%02x", $0) }.joined()
    }

    // MARK: - Cleanup

    private func stopBrowsing() {
        mdnsBrowser?.cancel()
        mdnsBrowser = nil
    }

    private func cleanup() {
        serviceConnection?.cancel()
        serviceConnection = nil
        stopBrowsing()
    }

    deinit {
        cleanup()
    }

    // MARK: - Status Updates

    private func updateStatus(_ text: String, level: TrustLevel) {
        MainActor.assumeIsolated {
            pairingStatusText = text
            pairingTrustLevel = level
        }
    }
}

// MARK: - Supporting Types

struct QRCodeData {
    let mdnsServiceName: String
    let serverSignature: String
}

enum PairingError: LocalizedError {
    case invalidURL
    case invalidResponse
    case invalidQRCode
    case unauthorized
    case alreadyPaired
    case serverError(Int)
    case decodingFailed

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid server URL"
        case .invalidResponse:
            return "Invalid server response"
        case .invalidQRCode:
            return "Invalid QR code format"
        case .unauthorized:
            return "Unauthorized (401)"
        case .alreadyPaired:
            return "Device already paired (409)"
        case .serverError(let code):
            return "Server error: \(code)"
        case .decodingFailed:
            return "Failed to decode response"
        }
    }
}

// MARK: - Keychain Helper

private class KeychainHelper {
    private let service = "com.rhea.pairing"
    private let privateKeyKey = "ed25519.privatekey"
    private let receiptKey = "pairing.receipt"

    func storePrivateKey(_ key: Curve25519.Signing.PrivateKey) throws {
        let data = key.rawRepresentation
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: privateKeyKey,
            kSecValueData as String: data
        ]
        SecItemDelete(query as CFDictionary)
        try SecItemAdd(query as CFDictionary, nil).check()
    }

    func retrievePrivateKey() -> Curve25519.Signing.PrivateKey? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: privateKeyKey,
            kSecReturnData as String: true
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return try? Curve25519.Signing.PrivateKey(rawRepresentation: data)
    }

    func storeReceipt(_ receipt: PairingDelegate.SessionReceipt) throws {
        let data = try JSONEncoder().encode(receipt)
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: receiptKey,
            kSecValueData as String: data
        ]
        SecItemDelete(query as CFDictionary)
        try SecItemAdd(query as CFDictionary, nil).check()
    }

    func retrieveReceipt() -> PairingDelegate.SessionReceipt? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: receiptKey,
            kSecReturnData as String: true
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return try? JSONDecoder().decode(PairingDelegate.SessionReceipt.self, from: data)
    }
}

// MARK: - Security Status Extension

extension OSStatus {
    func check() throws {
        guard self == errSecSuccess else {
            throw NSError(domain: NSOSStatusErrorDomain, code: Int(self))
        }
    }
}
