import SwiftUI

// MARK: - Unified Agent DTO
// Superset of GovernorView.AgentStatus + PulseAgentDTO + TeamChatView.UnifiedAgentDTO
// Extra fields from Governor are Optional so decoding from /agents/status works everywhere.

public struct AgentDTO: Codable, Identifiable {
    public var id: String { name }
    public let name: String
    public let alive: Bool
    public let pace: String
    public let mode: String
    public let billing_mode: String?
    public let T_day: Int
    public let dollar_day: Double
    public let floor_gap: Int
    public let office_status: String?
    public let pending_msgs: Int?
    public let tasks_open: Int?
    public let tasks_claimed: Int?
    public let last_activity: String?
    public let last_feed: String?

    // Lease fields (Pulse / TeamChat)
    public let lease_token: Int?
    public let lease_expired: Bool?
    public let lease_expires_at: String?

    // Governor-specific (Optional)
    public let forecast: String?
    public let upper_rail_enabled: Bool?
    public let budget_cap: Double?
    public let budget_remaining: Double?
    public let floor_expected: Int?
    public let hour: Int?
    public let hard_fail: Bool?

    // Compat: old GovernorView code uses .agent
    public var agent: String { name }

    // Safe accessor — defaults hard_fail to false when nil
    public var isHardFail: Bool { hard_fail ?? false }

    // Safe accessor — defaults lease_expired to false when nil
    public var isLeaseExpired: Bool { lease_expired ?? false }

    // Safe accessor — defaults lease_token to 0 when nil
    public var leaseTokenValue: Int { lease_token ?? 0 }

    // Safe accessors for non-optional usage (TeamChat / Pulse)
    public var officeStatus: String { office_status ?? "unknown" }
    public var pendingMsgs: Int { pending_msgs ?? 0 }
    public var tasksOpen: Int { tasks_open ?? 0 }
    public var tasksClaimed: Int { tasks_claimed ?? 0 }

    public init(name: String, alive: Bool, pace: String, mode: String, billing_mode: String?, T_day: Int, dollar_day: Double, floor_gap: Int, office_status: String?, pending_msgs: Int?, tasks_open: Int?, tasks_claimed: Int?, last_activity: String?, last_feed: String?, lease_token: Int?, lease_expired: Bool?, lease_expires_at: String?, forecast: String?, upper_rail_enabled: Bool?, budget_cap: Double?, budget_remaining: Double?, floor_expected: Int?, hour: Int?, hard_fail: Bool?) {
        self.name = name
        self.alive = alive
        self.pace = pace
        self.mode = mode
        self.billing_mode = billing_mode
        self.T_day = T_day
        self.dollar_day = dollar_day
        self.floor_gap = floor_gap
        self.office_status = office_status
        self.pending_msgs = pending_msgs
        self.tasks_open = tasks_open
        self.tasks_claimed = tasks_claimed
        self.last_activity = last_activity
        self.last_feed = last_feed
        self.lease_token = lease_token
        self.lease_expired = lease_expired
        self.lease_expires_at = lease_expires_at
        self.forecast = forecast
        self.upper_rail_enabled = upper_rail_enabled
        self.budget_cap = budget_cap
        self.budget_remaining = budget_remaining
        self.floor_expected = floor_expected
        self.hour = hour
        self.hard_fail = hard_fail
    }
}
