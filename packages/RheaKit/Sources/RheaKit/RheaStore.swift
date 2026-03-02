import SwiftUI
import GRDB
import Collections

/// The shared brain of Rhea Play UI.
/// One store, one polling loop, one source of truth.
/// All panes observe this — no duplicate fetchers.
///
/// Data tiers:
///   - Core (polled every 5s): agents, health, proof count
///   - On-demand (fetched when pane opens): history, radio, proofs, ontologies
///   - Ephemeral (never cached): SSE stream, active dialog
///
/// After a cloud restart, SQL-backed data (history, radio, proofs) is real.
/// In-memory server state (governor counters, agent leases) resets to zero.
/// The store tracks staleness per data type and triggers recovery triage
/// when connection comes back.
@MainActor
public final class RheaStore: ObservableObject {
    public static let shared = RheaStore()

    private let api = RheaAPI.shared
    private var pollTimer: Timer?

    public init() {}

    /// Local SQLite cache — mirrors server's rhea.db for offline access.
    /// GRDB gives typed Swift records over raw SQL.
    public let db: DatabaseQueue? = {
        let path = FileManager.default
            .urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
            .appendingPathComponent("rhea", isDirectory: true)
        try? FileManager.default.createDirectory(at: path, withIntermediateDirectories: true)
        let dbPath = path.appendingPathComponent("local.db").path
        guard let db = try? DatabaseQueue(path: dbPath) else { return nil }
        try? db.write { db in
            try db.execute(sql: """
                CREATE TABLE IF NOT EXISTS cached_proofs (
                    id TEXT PRIMARY KEY,
                    claim TEXT NOT NULL,
                    tier TEXT,
                    agreement_score REAL,
                    confidence REAL,
                    created_at TEXT,
                    data TEXT
                );
                CREATE TABLE IF NOT EXISTS cached_history (
                    id INTEGER PRIMARY KEY,
                    type TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    agreement_score REAL,
                    created_at TEXT,
                    data TEXT
                );
            """)
        }
        return db
    }()

    // ─── Core State (polled) ─────────────────────────────────────────

    @Published public var agents: [AgentDTO] = []
    @Published public var health: HealthSnapshot?
    @Published public var connectionAlive = false
    @Published public var proofCount = 0

    /// Agent lookup by name — O(1) access, preserves order.
    public private(set) var agentMap: OrderedDictionary<String, AgentDTO> = [:]

    // ─── Derived Metrics ─────────────────────────────────────────────

    public var totalTokens: Int { agents.reduce(0) { $0 + $1.T_day } }
    public var totalCost: Double { agents.reduce(0.0) { $0 + $1.dollar_day } }
    public var aliveCount: Int { agents.filter { $0.alive }.count }
    public var familyOnline: Bool { !agents.isEmpty && agents.allSatisfy { $0.alive } }

    // ─── Staleness Tracking ──────────────────────────────────────────

    private var lastFetch: [String: Date] = [:]
    private var wasOffline = false

    public func age(_ key: String) -> TimeInterval {
        guard let t = lastFetch[key] else { return .infinity }
        return Date().timeIntervalSince(t)
    }

    // ─── Polling Lifecycle ───────────────────────────────────────────

    public func startPolling(interval: TimeInterval = 5) {
        stopPolling()
        Task { await refreshCore() }
        pollTimer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                await self?.refreshCore()
            }
        }
    }

    public func stopPolling() {
        pollTimer?.invalidate()
        pollTimer = nil
    }

    // ─── Core Refresh (runs every 5s) ────────────────────────────────

    public func refreshCore() async {
        let wasAlive = connectionAlive

        // Agents
        do {
            let fetched = try await api.agents()
            agents = fetched
            agentMap = OrderedDictionary(uniqueKeysWithValues: fetched.map { ($0.name, $0) })
            connectionAlive = true
            lastFetch["agents"] = Date()
        } catch {
            connectionAlive = false
        }

        // Health (lightweight, same server round-trip window)
        do {
            health = try await api.health()
            lastFetch["health"] = Date()
        } catch {}

        // Proof count (single int, cheap)
        do {
            let p = try await api.proofs()
            proofCount = p.count
            lastFetch["proofCount"] = Date()
        } catch {}

        // Connection recovery detection
        if !wasAlive && connectionAlive {
            await onConnectionRecovered()
        }
        if wasAlive && !connectionAlive {
            wasOffline = true
        }
    }

    // ─── Connection Recovery ─────────────────────────────────────────

    /// TODO(human): Implement recovery triage — the cell stress response.
    ///
    /// After a cloud restart (Fly.io suspend/resume, Cloud Run cold start),
    /// ALL in-memory server state is gone:
    ///   - Governor token counters → reset to 0 (the zero IS truth)
    ///   - Agent leases → all expired (agents show dead until re-lease)
    ///   - SSE subscribers → disconnected (reconnect happens automatically)
    ///
    /// But SQL-backed data SURVIVED:
    ///   - Proofs (proof.db) → immutable, long half-life
    ///   - History (rhea.db) → append-only, need delta since last fetch
    ///   - Radio (rhea.db) → chronological, need delta
    ///   - Office messages → persisted, need delta
    ///
    /// Your task: decide the recovery order and staleness thresholds.
    /// Think of it like cellular stress recovery:
    ///   1. Membrane integrity → is the server even alive? (already done above)
    ///   2. Core metabolism → which data to refresh FIRST?
    ///   3. Clear damaged state → what cached data is now WRONG and must be invalidated?
    ///   4. Resume normal ops → when to flip back to normal polling?
    ///
    /// Fill in the body. You have access to:
    ///   - self.api (RheaAPI) for fetching
    ///   - self.lastFetch[key] for staleness
    ///   - self.age(key) returns seconds since last fetch
    ///   - self.wasOffline (true if we were previously disconnected)
    ///
    public func onConnectionRecovered() async {

    }

    // ─── On-Demand Refresh (called by panes) ─────────────────────────

    public func refreshHistory(limit: Int = 50) async -> [[String: Any]] {
        do {
            let h = try await api.history(limit: limit)
            lastFetch["history"] = Date()
            return h
        } catch { return [] }
    }

    public func refreshRadio(limit: Int = 100) async -> [[String: Any]] {
        do {
            let r = try await api.radio(limit: limit)
            lastFetch["radio"] = Date()
            return r
        } catch { return [] }
    }

    public func refreshProofs() async -> [[String: Any]] {
        do {
            let p = try await api.proofs()
            proofCount = p.count
            lastFetch["proofs"] = Date()
            return p
        } catch { return [] }
    }

    public func refreshOntologies() async -> [[String: Any]] {
        do {
            let o = try await api.ontologies()
            lastFetch["ontologies"] = Date()
            return o
        } catch { return [] }
    }

    // ─── Helpers ─────────────────────────────────────────────────────

    public func formatTokens(_ n: Int) -> String {
        if n >= 1_000_000 { return "\(n / 1_000_000)M" }
        if n >= 1_000 { return "\(n / 1_000)K" }
        return "\(n)"
    }
}
