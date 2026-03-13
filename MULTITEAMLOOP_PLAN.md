# RHEA MULTITEAMLOOP PLAN: The Balancer & Agent Orchestration

## 1. The Core Architecture: "The Balancer"
To prevent agent chaos, overlapping writes, and token waste, we are introducing **The Balancer** as the central nervous system. 

*   **Location:** Hosted on Google Cloud / Fly.io.
*   **Role:** The ultimate traffic controller and state lock manager.
*   **Mechanism:** It acts as a gateway for all agent-to-agent and agent-to-system operations.
*   **Write Privileges:** The Balancer holds the master lock. Local machine daemons (Windsurf, Roo, CLI) must request a lease via Redis to write to the filesystem or the DB. It can send `[allow/approval/okay]` or pause tasks that violate constraints.

## 2. The NDI & Bonjour Mesh Network
The `ndi_bridge.py` is not just for video. NDI (Network Device Interface) uses mDNS/Bonjour for zero-configuration discovery on local networks.
*   **The Use Case:** Agent session transferring and a cross-OS (Windows/Mac) shared clipboard.
*   **How it works:** The multi-OS daemon broadcasts its presence via Bonjour. When an agent on a Mac wants to send a complex object (like a compiled binary or a massive context payload) to a Windows agent, it establishes a high-bandwidth local NDI stream, bypassing the 30MB cloud limits.

## 3. The Multi-Team Loop: The Deterministic Pipeline
We are killing the "chat and guess" model. Every task follows this strict binary loop enforced by The Balancer:

1.  **[Prompt]**: Human (or Head Agent) injects the raw requirement into the `rhea:queue:jobs`.
2.  **[Enhance]**: A fast, cheap model (e.g., GPT-4o-mini via OpenRouter) enriches the prompt with context from LangCache (Semantic Memory).
3.  **[Extend]**: A reasoning model (DeepSeek R1 / Opus 4.6 via Roo/Windsurf) generates the code/AST/Proof.
4.  **[Compact]**: The Aletheia engine compresses the output into a verifiable SPR Hash and strips away conversational garbage.
5.  **[Check]**: The `rhea-tui` (operating as a VSCode extension overwrapper) runs local unit tests, Rust compilation, or Swift builds. If it fails, return to [Extend].
6.  **[Send]**: The Balancer approves the write. The payload is committed, and the next item in the loop begins.

## 4. TUI Overwrapper (VSCode Extension)
Models cannot be trusted to "respect" the rules voluntarily. The `rhea-tui` will be wrapped as a VSCode Extension.
*   **Function:** It intercepts file writes. If Windsurf tries to edit `src/core.rs` without holding the Balancer lock, the TUI extension blocks the file write at the OS level and returns a system error to the model: `ERROR: BALANCER LOCK REQUIRED.`

## 5. Next Execution Steps
1.  **Deploy The Balancer:** Scaffold the Fly.io deployment for the Balancer API.
2.  **VSCode Extension Scaffold:** Convert the TUI concept into a VSIX project to enforce write locks on Windsurf/Roo.
3.  **OpenRouter Integration:** Wire the `rhea_bridge.py` to dispatch tasks to Roo/Windsurf explicitly following the 6-step loop.
