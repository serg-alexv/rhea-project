import SwiftUI

// MARK: - Unified Agent DTO
// Superset of GovernorView.AgentStatus + PulseAgentDTO + TeamChatView.UnifiedAgentDTO
// Extra fields from Governor are Optional so decoding from /agents/status works everywhere.

struct AgentDTO: Codable, Identifiable {
    var id: String { name }
    let name: String
    let alive: Bool
    let pace: String
    let mode: String
    let billing_mode: String?
    let T_day: Int
    let dollar_day: Double
    let floor_gap: Int
    let office_status: String?
    let pending_msgs: Int?
    let tasks_open: Int?
    let tasks_claimed: Int?
    let last_activity: String?
    let last_feed: String?

    // Lease fields (Pulse / TeamChat)
    let lease_token: Int?
    let lease_expired: Bool?
    let lease_expires_at: String?

    // Governor-specific (Optional)
    let forecast: String?
    let upper_rail_enabled: Bool?
    let budget_cap: Double?
    let budget_remaining: Double?
    let floor_expected: Int?
    let hour: Int?
    let hard_fail: Bool?

    // Compat: old GovernorView code uses .agent
    var agent: String { name }

    // Safe accessor — defaults hard_fail to false when nil
    var isHardFail: Bool { hard_fail ?? false }

    // Safe accessor — defaults lease_expired to false when nil
    var isLeaseExpired: Bool { lease_expired ?? false }

    // Safe accessor — defaults lease_token to 0 when nil
    var leaseTokenValue: Int { lease_token ?? 0 }

    // Safe accessors for non-optional usage (TeamChat / Pulse)
    var officeStatus: String { office_status ?? "unknown" }
    var pendingMsgs: Int { pending_msgs ?? 0 }
    var tasksOpen: Int { tasks_open ?? 0 }
    var tasksClaimed: Int { tasks_claimed ?? 0 }
}
