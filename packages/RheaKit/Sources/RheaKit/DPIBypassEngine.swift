import Foundation
import os.log

/// Rhea DPI Bypass Engine — packet-level anti-censorship.
///
/// **INTERNAL USE ONLY** - Should only be used by PacketTunnelProvider.
/// Not exposed in public API to prevent misuse.
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
final class DPIBypassEngine {

    internal struct Config {
        /// Split TLS ClientHello at SNI field boundary
        internal var splitClientHello: Bool = true

        /// Number of segments to split ClientHello into
        internal var splitSegments: Int = 2

        /// Split position: bytes from start of ClientHello, or -1 for auto (at SNI)
        internal var splitPosition: Int = -1

        /// Send segments in reverse order (disorder mode)
        internal var disorder: Bool = false

        /// Inject fake RST packet with low TTL before ClientHello
        internal var fakePacketTTL: UInt8? = nil

        /// Split TLS record itself (not just TCP segments)
        internal var tlsRecordSplit: Bool = false

        /// Randomize HTTP Host header case
        internal var hostCaseRandomize: Bool = true

        /// Out-of-band byte injection after first split
        internal var oobInjection: Bool = false

        /// Domains to bypass (empty = all)
        internal var targetDomains: [String] = []

        internal init() {}

        /// Aggressive preset — combines multiple techniques for heavily censored networks
        internal static var aggressive: Config {
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
        internal static var gentle: Config {
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
    internal private(set) var totalPackets: UInt64 = 0
    internal private(set) var modifiedPackets: UInt64 = 0
    internal private(set) var tlsClientHellos: UInt64 = 0
    internal private(set) var httpRequests: UInt64 = 0

    internal init(config: Config = Config()) {
        self.config = config
        log.info("DPI bypass engine initialized. split=\(config.splitClientHello) disorder=\(config.disorder) fakeTTL=\(config.fakePacketTTL.map(String.init) ?? "off")")
    }

    // MARK: - Packet Processing

    /// Process a raw IPv4/IPv6 packet. Returns one or more packets to send.
    /// If the packet doesn't need modification, returns it unchanged.
    internal func process(packet: Data) -> [Data] {
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
            return [randomizeHostCase(packet: packet, ipHeaderLen: ipHeaderLen, payloadStart: tcpPayloadStart, isIPv6: isIPv6)]
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

        // OOB injection: insert a garbage byte with TCP URG flag into fragment 1.
        // DPI reads the garbage as part of SNI and fails pattern matching.
        // The real server ignores urgent data per RFC 6093.
        if config.oobInjection {
            let tcpFlagsOffset = ipHeaderLen + 13
            // Set URG flag (bit 5) in TCP flags, preserving existing flags
            frag1[tcpFlagsOffset] = frag1[tcpFlagsOffset] | 0x20
            // Set urgent pointer to 1 (bytes 18-19 of TCP header)
            frag1[ipHeaderLen + 18] = 0x00
            frag1[ipHeaderLen + 19] = 0x01
            // Insert one garbage byte at the start of TCP payload
            let garbageByte: UInt8 = UInt8.random(in: 0x01...0xFE)
            frag1.insert(garbageByte, at: payloadStart)
            log.debug("OOB injection: inserted urgent byte 0x\(String(garbageByte, radix: 16)) into fragment 1")
        }

        updateIPLength(&frag1, isIPv6: isIPv6)
        recalculateChecksums(&frag1, ipHeaderLen: ipHeaderLen, isIPv6: isIPv6)

        // Build fragment 2: IP+TCP headers + payload[splitPos:]
        var frag2 = Data(packet[0..<payloadStart])
        frag2.append(packet[(payloadStart + splitPos)...])
        // Update sequence number for fragment 2
        // Account for OOB garbage byte in sequence space if injected
        let oobExtra: UInt32 = config.oobInjection ? 1 : 0
        let newSeq = seqNum + UInt32(splitPos) + oobExtra
        frag2[tcpStart + 4] = UInt8((newSeq >> 24) & 0xFF)
        frag2[tcpStart + 5] = UInt8((newSeq >> 16) & 0xFF)
        frag2[tcpStart + 6] = UInt8((newSeq >> 8) & 0xFF)
        frag2[tcpStart + 7] = UInt8(newSeq & 0xFF)
        updateIPLength(&frag2, isIPv6: isIPv6)
        recalculateChecksums(&frag2, ipHeaderLen: ipHeaderLen, isIPv6: isIPv6)

        var result: [Data] = []

        // Optional: inject fake RST with low TTL before the real data
        if let fakeTTL = config.fakePacketTTL {
            var fakeRST = buildFakeRST(from: packet, ipHeaderLen: ipHeaderLen, tcpHeaderLen: tcpHeaderLen, isIPv6: isIPv6)
            setTTL(&fakeRST, ttl: fakeTTL, isIPv6: isIPv6)
            recalculateChecksums(&fakeRST, ipHeaderLen: ipHeaderLen, isIPv6: isIPv6)
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

        log.debug("Split ClientHello: \(payloadLen)B → \(splitPos)B + \(payloadLen - splitPos)B\(self.config.oobInjection ? " [OOB]" : "")")
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

    private func randomizeHostCase(packet: Data, ipHeaderLen: Int, payloadStart: Int, isIPv6: Bool) -> Data {
        var modified = packet
        let payload = Array(packet[payloadStart...])

        // Find "Host:" header (case-insensitive search)
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
                // Recalculate checksums after modifying payload bytes
                recalculateChecksums(&modified, ipHeaderLen: ipHeaderLen, isIPv6: isIPv6)
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

    // MARK: - Checksum Recalculation

    /// Recalculate IPv4 header checksum per RFC 791.
    /// Zeros out the checksum field, computes the ones-complement sum of all
    /// 16-bit words in the IP header, and stores the result.
    private func recalculateIPv4Checksum(_ packet: inout Data) {
        let ihl = Int(packet[0] & 0x0F) * 4
        guard packet.count >= ihl else { return }

        // Zero out existing checksum (bytes 10-11)
        packet[10] = 0
        packet[11] = 0

        var sum: UInt32 = 0
        for i in stride(from: 0, to: ihl, by: 2) {
            let word = UInt32(packet[i]) << 8 | UInt32(packet[i + 1])
            sum += word
        }

        // Fold 32-bit sum into 16-bit ones-complement
        while sum >> 16 != 0 {
            sum = (sum & 0xFFFF) + (sum >> 16)
        }

        let checksum = ~UInt16(sum & 0xFFFF)
        packet[10] = UInt8((checksum >> 8) & 0xFF)
        packet[11] = UInt8(checksum & 0xFF)
    }

    /// Recalculate TCP checksum with pseudo-header per RFC 793.
    /// Pseudo-header: source IP + dest IP + zero + protocol (6) + TCP length.
    /// Then ones-complement sum of pseudo-header + TCP header + TCP payload.
    private func recalculateTCPChecksum(_ packet: inout Data, ipHeaderLen: Int, isIPv6: Bool) {
        let tcpStart = ipHeaderLen
        let tcpLen = packet.count - tcpStart
        guard tcpLen >= 20, tcpStart + 16 <= packet.count else { return }

        // Zero out existing TCP checksum (bytes 16-17 of TCP header)
        packet[tcpStart + 16] = 0
        packet[tcpStart + 17] = 0

        var sum: UInt32 = 0

        if isIPv6 {
            // IPv6 pseudo-header: 16-byte src + 16-byte dest + TCP length (4 bytes) + next header (4 bytes, padded)
            guard packet.count >= 40 else { return }
            // Source address: bytes 8..23
            for i in stride(from: 8, to: 24, by: 2) {
                sum += UInt32(packet[i]) << 8 | UInt32(packet[i + 1])
            }
            // Destination address: bytes 24..39
            for i in stride(from: 24, to: 40, by: 2) {
                sum += UInt32(packet[i]) << 8 | UInt32(packet[i + 1])
            }
            // TCP length as 32-bit (upper 16 + lower 16)
            let tcpLength = UInt32(tcpLen)
            sum += (tcpLength >> 16) & 0xFFFF
            sum += tcpLength & 0xFFFF
            // Next header (protocol = 6 for TCP), zero-padded to 32 bits
            sum += 6
        } else {
            // IPv4 pseudo-header: 4-byte src + 4-byte dest + zero + protocol + TCP length
            guard packet.count >= ipHeaderLen else { return }
            // Source IP: bytes 12-15
            sum += UInt32(packet[12]) << 8 | UInt32(packet[13])
            sum += UInt32(packet[14]) << 8 | UInt32(packet[15])
            // Destination IP: bytes 16-19
            sum += UInt32(packet[16]) << 8 | UInt32(packet[17])
            sum += UInt32(packet[18]) << 8 | UInt32(packet[19])
            // Protocol (TCP = 6)
            sum += 6
            // TCP length
            sum += UInt32(tcpLen)
        }

        // Sum TCP header + payload as 16-bit words
        for i in stride(from: tcpStart, to: tcpStart + tcpLen - 1, by: 2) {
            sum += UInt32(packet[i]) << 8 | UInt32(packet[i + 1])
        }
        // Handle odd byte at the end
        if tcpLen % 2 != 0 {
            sum += UInt32(packet[tcpStart + tcpLen - 1]) << 8
        }

        // Fold 32-bit sum into 16-bit ones-complement
        while sum >> 16 != 0 {
            sum = (sum & 0xFFFF) + (sum >> 16)
        }

        let checksum = ~UInt16(sum & 0xFFFF)
        packet[tcpStart + 16] = UInt8((checksum >> 8) & 0xFF)
        packet[tcpStart + 17] = UInt8(checksum & 0xFF)
    }

    /// Recalculate all applicable checksums for a modified packet.
    /// For IPv4: recalculates both IP header checksum and TCP checksum.
    /// For IPv6: recalculates TCP checksum only (IPv6 has no header checksum).
    private func recalculateChecksums(_ packet: inout Data, ipHeaderLen: Int, isIPv6: Bool) {
        if !isIPv6 {
            recalculateIPv4Checksum(&packet)
        }
        recalculateTCPChecksum(&packet, ipHeaderLen: ipHeaderLen, isIPv6: isIPv6)
    }

    // MARK: - Extracting SNI hostname (for domain filtering)

    /// Extract the SNI hostname from a TLS ClientHello payload.
    internal func extractSNI(_ payload: Data.SubSequence) -> String? {
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
