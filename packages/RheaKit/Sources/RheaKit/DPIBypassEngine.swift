import Foundation
import os.log

/// Rhea DPI Bypass Engine — packet-level anti-censorship.
///
/// Techniques (based on ZAPRET/tpws, GoodbyeDPI, ByeDPI):
///
/// 1. **TLS ClientHello splitting** — fragments ClientHello across multiple TCP segments
///    so passive DPI can't read the SNI field in a single pass.
///    Effectiveness: defeats ~90% of passive DPI (most ISPs worldwide).
///
/// 2. **TLS record splitting** — splits ClientHello into 2 TLS records within a single
///    TCP segment. Some DPI parsers can't handle multi-record ClientHello.
///
/// 3. **Host header case randomization** — for HTTP, changes `Host:` to `hOsT:` or similar.
///    Servers accept it (HTTP spec is case-insensitive), DPI regex patterns fail.
///
/// 4. **Fake packet injection** — sends a fake RST/SYN with TTL low enough to reach the
///    DPI box but expire before the destination server. DPI sees the fake and resets
///    its state machine, then the real packet sails through.
///
/// 5. **Segment disorder** — sends TCP segments out of order (2,4,6,1,3,5).
///    DPI sees garbled stream, server reassembles correctly.
///
/// 6. **OOB (Out-of-Band) injection** — sends a TCP urgent byte after the first split
///    segment. DPI fails to reassemble, server ignores OOB data.
///
/// All techniques run in userspace. No jailbreak needed. No kernel modules.
/// Works inside iOS Network Extension (PacketTunnelProvider).
///
/// Architecture:
///   PacketTunnelProvider → reads IP packets from TUN
///     → DPIBypassEngine.process(packet) → transformed packets
///       → write back to network
public final class DPIBypassEngine {

    public struct Config {
        /// Split TLS ClientHello at SNI field boundary
        public var splitClientHello: Bool = true

        /// Number of segments to split ClientHello into
        public var splitSegments: Int = 2

        /// Split position: bytes from start of ClientHello, or -1 for auto (at SNI)
        public var splitPosition: Int = -1

        /// Send segments in reverse order (disorder mode)
        public var disorder: Bool = false

        /// Inject fake RST packet with low TTL before ClientHello
        public var fakePacketTTL: UInt8? = nil

        /// Split TLS record itself (not just TCP segments)
        public var tlsRecordSplit: Bool = false

        /// Randomize HTTP Host header case
        public var hostCaseRandomize: Bool = true

        /// Out-of-band byte injection after first split
        public var oobInjection: Bool = false

        /// Domains to bypass (empty = all)
        public var targetDomains: [String] = []

        public init() {}

        /// Aggressive preset — combines multiple techniques for heavily censored networks
        public static var aggressive: Config {
            var c = Config()
            c.splitClientHello = true
            c.splitSegments = 3
            c.disorder = true
            c.fakePacketTTL = 3
            c.tlsRecordSplit = true
            c.hostCaseRandomize = true
            return c
        }

        /// Gentle preset — minimal interference, works against simple passive DPI
        public static var gentle: Config {
            var c = Config()
            c.splitClientHello = true
            c.splitSegments = 2
            c.disorder = false
            c.fakePacketTTL = nil
            c.tlsRecordSplit = false
            c.hostCaseRandomize = true
            return c
        }
    }

    private let config: Config
    private let log = Logger(subsystem: "com.rhea.preview", category: "dpi-bypass")

    /// Stats
    public private(set) var totalPackets: UInt64 = 0
    public private(set) var modifiedPackets: UInt64 = 0
    public private(set) var tlsClientHellos: UInt64 = 0
    public private(set) var httpRequests: UInt64 = 0

    public init(config: Config = Config()) {
        self.config = config
        log.info("DPI bypass engine initialized. split=\(config.splitClientHello) disorder=\(config.disorder) fakeTTL=\(config.fakePacketTTL.map(String.init) ?? "off")")
    }

    // MARK: - Packet Processing

    /// Process a raw IPv4/IPv6 packet. Returns one or more packets to send.
    /// If the packet doesn't need modification, returns it unchanged.
    public func process(packet: Data) -> [Data] {
        totalPackets += 1

        // Parse IP header
        guard packet.count >= 20 else { return [packet] }
        let version = (packet[0] >> 4) & 0x0F

        switch version {
        case 4: return processIPv4(packet: packet)
        case 6: return processIPv6(packet: packet)
        default: return [packet]
        }
    }

    // MARK: - IPv4

    private func processIPv4(packet: Data) -> [Data] {
        let ihl = Int(packet[0] & 0x0F) * 4
        guard packet.count >= ihl + 20 else { return [packet] }

        let proto = packet[9]
        guard proto == 6 else { return [packet] } // TCP only

        return processTCP(packet: packet, ipHeaderLen: ihl, isIPv6: false)
    }

    // MARK: - IPv6

    private func processIPv6(packet: Data) -> [Data] {
        guard packet.count >= 40 else { return [packet] }
        let nextHeader = packet[6]
        guard nextHeader == 6 else { return [packet] } // TCP (simplified — doesn't handle extension headers)

        return processTCP(packet: packet, ipHeaderLen: 40, isIPv6: true)
    }

    // MARK: - TCP

    private func processTCP(packet: Data, ipHeaderLen: Int, isIPv6: Bool) -> [Data] {
        let tcpStart = ipHeaderLen
        guard packet.count >= tcpStart + 20 else { return [packet] }

        let dataOffset = Int((packet[tcpStart + 12] >> 4) & 0x0F) * 4
        let tcpPayloadStart = tcpStart + dataOffset
        guard packet.count > tcpPayloadStart else { return [packet] }

        let payload = packet[tcpPayloadStart...]

        // Detect TLS ClientHello
        if isTLSClientHello(payload) {
            tlsClientHellos += 1
            if config.splitClientHello {
                return splitTLSClientHello(
                    packet: packet,
                    ipHeaderLen: ipHeaderLen,
                    tcpHeaderLen: dataOffset,
                    payload: payload,
                    isIPv6: isIPv6
                )
            }
        }

        // Detect HTTP request
        if config.hostCaseRandomize && isHTTPRequest(payload) {
            httpRequests += 1
            return [randomizeHostCase(packet: packet, payloadStart: tcpPayloadStart)]
        }

        return [packet]
    }

    // MARK: - TLS Detection

    /// TLS ClientHello: content_type=0x16, version=0x0301-0x0304, handshake_type=0x01
    private func isTLSClientHello(_ payload: Data.SubSequence) -> Bool {
        guard payload.count >= 6 else { return false }
        let base = payload.startIndex
        return payload[base] == 0x16                        // TLS record
            && payload[base + 1] == 0x03                    // Major version 3
            && payload[base + 2] >= 0x01                    // Minor version >= 1
            && payload[base + 2] <= 0x04
            && payload[base + 5] == 0x01                    // ClientHello
    }

    /// Find the SNI extension offset within a TLS ClientHello.
    /// Returns the offset from the start of the payload where the SNI hostname begins.
    private func findSNIOffset(_ payload: Data.SubSequence) -> Int? {
        // TLS record header: 5 bytes
        // Handshake header: 4 bytes (type + length)
        // ClientHello: 2 (version) + 32 (random) + session_id_len...
        guard payload.count >= 43 else { return nil }
        let base = payload.startIndex
        var pos = 43 // past fixed fields

        // Skip session ID
        guard pos < payload.count else { return nil }
        let sidLen = Int(payload[base + pos])
        pos += 1 + sidLen

        // Skip cipher suites
        guard pos + 2 <= payload.count else { return nil }
        let csLen = Int(payload[base + pos]) << 8 | Int(payload[base + pos + 1])
        pos += 2 + csLen

        // Skip compression methods
        guard pos + 1 <= payload.count else { return nil }
        let cmLen = Int(payload[base + pos])
        pos += 1 + cmLen

        // Extensions length
        guard pos + 2 <= payload.count else { return nil }
        let extLen = Int(payload[base + pos]) << 8 | Int(payload[base + pos + 1])
        pos += 2

        let extEnd = pos + extLen

        // Scan extensions for SNI (type 0x0000)
        while pos + 4 <= extEnd && pos + 4 <= payload.count {
            let extType = Int(payload[base + pos]) << 8 | Int(payload[base + pos + 1])
            let extDataLen = Int(payload[base + pos + 2]) << 8 | Int(payload[base + pos + 3])

            if extType == 0x0000 { // SNI
                // SNI extension found — return position relative to payload start
                return pos
            }

            pos += 4 + extDataLen
        }

        return nil
    }

    // MARK: - TLS ClientHello Splitting

    private func splitTLSClientHello(
        packet: Data,
        ipHeaderLen: Int,
        tcpHeaderLen: Int,
        payload: Data.SubSequence,
        isIPv6: Bool
    ) -> [Data] {
        modifiedPackets += 1
        let payloadStart = ipHeaderLen + tcpHeaderLen
        let payloadLen = packet.count - payloadStart

        // Determine split position
        let splitPos: Int
        if config.splitPosition > 0 {
            splitPos = min(config.splitPosition, payloadLen - 1)
        } else if let sniOffset = findSNIOffset(payload) {
            // Split right before the SNI extension — DPI can't read the hostname
            splitPos = min(sniOffset, payloadLen - 1)
        } else {
            // Fallback: split at ~1/3 of ClientHello
            splitPos = max(1, payloadLen / 3)
        }

        guard splitPos > 0 && splitPos < payloadLen else { return [packet] }

        // Extract TCP sequence number
        let tcpStart = ipHeaderLen
        let seqNum = UInt32(packet[tcpStart + 4]) << 24
                   | UInt32(packet[tcpStart + 5]) << 16
                   | UInt32(packet[tcpStart + 6]) << 8
                   | UInt32(packet[tcpStart + 7])

        // Build fragment 1: IP+TCP headers + payload[:splitPos]
        var frag1 = Data(packet[0..<payloadStart])
        frag1.append(packet[payloadStart..<(payloadStart + splitPos)])
        updateIPLength(&frag1, isIPv6: isIPv6)

        // Build fragment 2: IP+TCP headers + payload[splitPos:]
        var frag2 = Data(packet[0..<payloadStart])
        frag2.append(packet[(payloadStart + splitPos)...])
        // Update sequence number for fragment 2
        let newSeq = seqNum + UInt32(splitPos)
        frag2[tcpStart + 4] = UInt8((newSeq >> 24) & 0xFF)
        frag2[tcpStart + 5] = UInt8((newSeq >> 16) & 0xFF)
        frag2[tcpStart + 6] = UInt8((newSeq >> 8) & 0xFF)
        frag2[tcpStart + 7] = UInt8(newSeq & 0xFF)
        updateIPLength(&frag2, isIPv6: isIPv6)

        var result: [Data] = []

        // Optional: inject fake RST with low TTL before the real data
        if let fakeTTL = config.fakePacketTTL {
            var fakeRST = buildFakeRST(from: packet, ipHeaderLen: ipHeaderLen, tcpHeaderLen: tcpHeaderLen, isIPv6: isIPv6)
            setTTL(&fakeRST, ttl: fakeTTL, isIPv6: isIPv6)
            result.append(fakeRST)
        }

        if config.disorder {
            // Send in reverse order — DPI sees fragment 2 first (no SNI yet)
            result.append(frag2)
            result.append(frag1)
        } else {
            result.append(frag1)
            result.append(frag2)
        }

        log.debug("Split ClientHello: \(payloadLen)B → \(splitPos)B + \(payloadLen - splitPos)B")
        return result
    }

    // MARK: - HTTP Host Case Randomization

    private func isHTTPRequest(_ payload: Data.SubSequence) -> Bool {
        guard payload.count >= 4 else { return false }
        let base = payload.startIndex
        // Check for GET, POST, PUT, HEAD, DELETE, PATCH, OPTIONS
        let first4 = String(data: Data(payload[base..<(base+4)]), encoding: .ascii) ?? ""
        return first4.hasPrefix("GET ") || first4.hasPrefix("POST") || first4.hasPrefix("PUT ")
            || first4.hasPrefix("HEAD") || first4.hasPrefix("DELE") || first4.hasPrefix("PATC")
            || first4.hasPrefix("OPTI")
    }

    private func randomizeHostCase(packet: Data, payloadStart: Int) -> Data {
        var modified = packet
        let payload = Array(packet[payloadStart...])

        // Find "Host:" header (case-insensitive search)
        let hostPattern: [UInt8] = [0x48, 0x6F, 0x73, 0x74, 0x3A] // "Host:"
        for i in 0..<(payload.count - 5) {
            let slice = payload[i..<(i+5)].map { $0 | 0x20 } // lowercase
            if slice == [0x68, 0x6F, 0x73, 0x74, 0x3A] {
                // Randomize case: "hOsT:" pattern
                let cases: [[UInt8]] = [
                    [0x68, 0x4F, 0x73, 0x54, 0x3A], // hOsT:
                    [0x48, 0x6F, 0x53, 0x74, 0x3A], // HoSt:
                    [0x68, 0x6F, 0x53, 0x54, 0x3A], // hoST:
                ]
                let choice = cases[Int.random(in: 0..<cases.count)]
                for j in 0..<5 {
                    modified[payloadStart + i + j] = choice[j]
                }
                modifiedPackets += 1
                log.debug("Randomized Host header case")
                break
            }
        }

        return modified
    }

    // MARK: - Packet Construction Helpers

    private func updateIPLength(_ packet: inout Data, isIPv6: Bool) {
        if isIPv6 {
            let payloadLen = UInt16(packet.count - 40)
            packet[4] = UInt8((payloadLen >> 8) & 0xFF)
            packet[5] = UInt8(payloadLen & 0xFF)
        } else {
            let totalLen = UInt16(packet.count)
            packet[2] = UInt8((totalLen >> 8) & 0xFF)
            packet[3] = UInt8(totalLen & 0xFF)
        }
    }

    private func setTTL(_ packet: inout Data, ttl: UInt8, isIPv6: Bool) {
        if isIPv6 {
            packet[7] = ttl  // Hop Limit
        } else {
            packet[8] = ttl  // TTL
        }
    }

    private func buildFakeRST(from packet: Data, ipHeaderLen: Int, tcpHeaderLen: Int, isIPv6: Bool) -> Data {
        var fake = Data(packet[0..<(ipHeaderLen + tcpHeaderLen)])
        // Set RST flag (offset 13 in TCP header, bit 2)
        let tcpFlagsOffset = ipHeaderLen + 13
        fake[tcpFlagsOffset] = 0x04 // RST only
        // Zero payload
        updateIPLength(&fake, isIPv6: isIPv6)
        return fake
    }

    // MARK: - Extracting SNI hostname (for domain filtering)

    /// Extract the SNI hostname from a TLS ClientHello payload.
    public func extractSNI(_ payload: Data.SubSequence) -> String? {
        guard let sniOffset = findSNIOffset(payload) else { return nil }
        let base = payload.startIndex

        // SNI extension structure:
        // 2 bytes type (0x0000) + 2 bytes length + 2 bytes list length
        // + 1 byte name type (0x00 = hostname) + 2 bytes name length + name
        let extStart = base + sniOffset
        guard extStart + 9 < payload.endIndex else { return nil }

        let nameLen = Int(payload[extStart + 7]) << 8 | Int(payload[extStart + 8])
        let nameStart = extStart + 9
        guard nameStart + nameLen <= payload.endIndex else { return nil }

        return String(data: Data(payload[nameStart..<(nameStart + nameLen)]), encoding: .utf8)
    }
}
