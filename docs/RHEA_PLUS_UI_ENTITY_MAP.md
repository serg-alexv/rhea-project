# Rhea Plus iOS -- Complete UI Entity Map

Generated: 2026-03-01 | Branch: stage4-release | Build: v1.0 (7)

---

## 1. Source File Inventory

| File | Lines | Purpose |
|------|------:|---------|
| `Sources/RheaPreviewApp.swift` | 281 | App entry, TabView shell, IntentEntryView onboarding |
| `Sources/Theme.swift` | 73 | RheaTheme color system + GlassCard modifier |
| `Sources/AppConfig.swift` | 56 | API base URLs, simulator/device detection, stale-URL migration |
| `Sources/DialogView.swift` | 340 | 1:1 chat with LLM tribunal (Dialog tab) |
| `Sources/TeamChatView.swift` | 957 | Live radio feed console + bubble mode (Team/Radio tab) |
| `Sources/GovernorView.swift` | 350 | Token governor dashboard per agent (Governor tab) |
| `Sources/TasksView.swift` | 216 | Task queue with filter chips (Tasks tab) |
| `Sources/AtlasWebView.swift` | 44 | WKWebView wrapper for Atlas frontend (Atlas tab) |
| `Sources/PulseMonitorView.swift` | 406 | Ops risk dashboard + flicker control (Pulse tab) |
| `Sources/ScreenPilotView.swift` | 234 | Remote screen-pilot mode (screenshot + tap commands) |
| `Sources/SettingsView.swift` | 187 | All user-configurable settings |
| `Package.swift` | 50 | Swift Package (SPM iOSApplication target) |
| **Total source** | **3,194** | 11 Swift files |

Config files:

| File | Lines | Purpose |
|------|------:|---------|
| `ios/RheaApp/project.yml` | 46 | xcodegen project definition for App Store build |
| `ios/RheaApp/Info.plist` | 40 | ATS local networking, orientations, display name |
| `ios/RheaApp/ExportOptions.plist` | -- | IPA export (app-store-connect, auto signing) |
| `ios/rhea-plus-ui/Package.swift` | 47 | RheaPlusUI umbrella library (re-exports 8 packages) |
| `ios/rhea-plus-ui/Sources/RheaPlusUI.swift` | 12 | @_exported imports for all 8 dependencies |

---

## 2. View Hierarchy Tree

```
RheaPreviewApp (@main)
|
+-- [Gate] hasEnteredIntent == false?
|     \-- IntentEntryView
|           |-- routeGrid (4 IntentRoute cards)
|           |-- TextField (base query)
|           |-- "Start" button --> POST /dialog
|           \-- "Expert" button --> bypass to revealLevel=3
|
+-- [Gate] hasEnteredIntent == true?
      \-- MainTabShell (TabView, dark scheme)
            |
            |-- Tab 0: DialogView              [always visible]
            |     |-- agentPicker (shared/rex/orion/gemini/hyperion)
            |     |-- messageList (ScrollView + LazyVStack of bubbles)
            |     \-- inputBar (TextField + send button)
            |
            |-- Tab 1: TeamChatView            [always visible]
            |     |-- onAirBanner (pulsing red dot, active agents)
            |     |-- tableExperimentBanner (TABLE session tracker)
            |     |-- filterBar (agent filter chips)
            |     |-- ScrollView
            |     |     |-- [toggle] ConsoleLine (terminal-style)
            |     |     \-- [toggle] BubbleLine  (chat-style)
            |     |-- composerBar
            |     \-- .sheet: agentSheet
            |           \-- List of RadioAgentInfo rows + WAKE button
            |
            |-- Tab 2: GovernorView            [revealLevel >= 2]
            |     |-- summaryHeader (MetricPill row)
            |     \-- LazyVStack of AgentCard
            |           |-- pace dot + mode badge
            |           |-- budget gauge (GeometryReader bar)
            |           |-- office status enrichment
            |           |-- StatChip row (tokens, hour, floor_gap)
            |           \-- AgentActionButton: Wake, Ping
            |
            |-- Tab 3: TasksView              [revealLevel >= 2]
            |     |-- FilterChip bar (All/Open/Claimed/Done/Blocked)
            |     \-- LazyVStack of TaskCard
            |           |-- priority ring + status icon
            |           |-- title, priority badge, claimed_by, tags
            |           \-- Pow .rise effect on "done"
            |
            |-- Tab 4: AtlasView             [revealLevel >= 3]
            |     \-- AtlasWebView (WKWebView -> atlasBaseURL + "/")
            |
            |-- Tab 5: PulseMonitorView       [revealLevel >= 3]
            |     |-- pulseHeader (Risk/Open/P0/Stale/Offline pills)
            |     |-- tableControlCard (SeatToggle per agent)
            |     |-- flickerControlCard (Mark Flicker / Wake REX / Create Trace Task)
            |     |-- queueCard (QueueRow list)
            |     \-- agentsCard (per-agent pace/mode/office row + Wake)
            |
            \-- Tab 6: SettingsView           [always visible]
                  |-- Atlas Web URL field
                  |-- API Base URL field + test connection
                  |-- "Use Cloud Run" shortcut
                  |-- Intent-First UX controls (reveal level, role, reset)
                  |-- Family Table Composition toggles
                  \-- Family Visibility Scope toggles
```

**ScreenPilotView**: Defined but NOT wired into any tab. Orphan view -- accessible only by direct instantiation.

---

## 3. Entity Relationship Diagram (ASCII)

```
+==================+     +==================+     +===================+
|  RheaPreviewApp  |     |   AppConfig      |     |    RheaTheme      |
|  (@main)         |---->| .defaultAPIBase  |     |  .bg .card .accent|
|  hasEnteredIntent|     | .productionAPI   |     |  .green .amber    |
|  intentRevealLvl |     | .defaultAtlasURL |     |  .red             |
|  selectedTab     |     | .migrateStale()  |     |  modeColor()      |
+==================+     +==================+     |  paceColor()      |
        |                                         |  priorityColor()  |
        v                                         |  statusColor()    |
+------------------+                              +===================+
| IntentEntryView  |                                       |
|  intentText      |                              +--------+--------+
|  isSending       |                              | GlassCard       |
|  errorText       |                              | (ViewModifier)  |
|  routes[]        |                              +-----------------+
| IntentRoute{4}   |
+--------+---------+
         |
         v
+------------------+     +--------------------+     +------------------+
| MainTabShell     |---->| DialogView         |     | TeamChatView     |
| selectedTab      |     | messages: [ChatMsg]|     | items:[FeedItem] |
| revealLevel      |     | inputText          |     | activeSenders    |
+------------------+     | targetAgent        |     | showBubbles      |
                         | agentResponse      |     | filterAgent      |
                         | pollTimer          |     | composerText     |
                         +--------+-----------+     | knownAgents      |
                                  |                 | wakingAgent      |
                    +-------------+------+          | tableTurn        |
                    |                    |          | tableSessionID   |
             +------+-------+  +--------+----+    +--------+----------+
             | ChatMsg      |  | DialogReq   |             |
             | id,sender    |  | text,sender  |    +--------+---------+
             | text,ts      |  +--------------+    |                  |
             +--------------+  | DialogResp   |  +-+----------+ +----+----------+
                               | reply,agree  |  | FeedItem   | | RadioAgentInfo|
                               | models_resp  |  | id,type    | | name,alive    |
                               | elapsed_s,ts |  | sender     | | pace,mode     |
                               +--------------+  | receiver   | | billingMode   |
                                                  | text,ts    | | tDay,dollarDay|
                    +------------------+          +------------+ | floorGap      |
                    | GovernorView     |                         | leaseToken    |
                    | agents:          |  +-------------------+  | officeStatus  |
                    | [AgentStatus]    |  | PulseMonitorView  |  | pendingMsgs   |
                    | loading          |  | summary:          |  | tasksOpen     |
                    | refreshCount     |  | PulseQueueSummary |  | tasksClaimed  |
                    +--------+---------+  | agents:           |  +---------------+
                             |            | [PulseAgentDTO]   |
                    +--------+---------+  | lastAction        |
                    | AgentStatus      |  | flickerNote       |
                    | name,alive       |  +--------+----------+
                    | pace,forecast    |           |
                    | mode,billing_mode|  +--------+-----------+
                    | T_day,dollar_day |  | PulseQueueSummary  |
                    | budget_cap/rem   |  | total, counts{}    |
                    | floor_gap,hour   |  | active_by_priority |
                    | office_status    |  | stale_count        |
                    | pending_msgs     |  +--------------------+
                    | tasks_open/claim |  | PulseAgentDTO      |
                    | hard_fail        |  | (same fields as    |
                    +------------------+  |  UnifiedAgentDTO)  |
                                          +--------------------+
                    +------------------+
                    | TasksView        |  +------------------+
                    | tasks:[TaskItem] |  | ScreenPilotView  |
                    | loading          |  | isRecording      |
                    | filter           |  | isPilotActive    |
                    +--------+---------+  | lastCommand      |
                             |            | tapIndicator     |
                    +--------+---------+  | statusText       |
                    | TaskItem         |  +--------+---------+
                    | id,title         |           |
                    | priority,status  |  +--------+---------+
                    | agent,claimed_by |  | PilotCommand     |
                    | tags[]           |  | id,action        |
                    +------------------+  | x,y,x2,y2       |
                                          | text,ts          |
                    +------------------+  +------------------+
                    | AtlasView        |
                    | atlasBaseURL     |
                    \-- AtlasWebView   |
                    +------------------+

                    +------------------+
                    | SettingsView     |
                    | draftAtlas       |
                    | draftAPI         |
                    | connectionStatus |
                    +------------------+
```

---

## 4. Complete Data Model Catalog

### DTOs (Codable structs for API responses)

| Model | File | Fields | Used By |
|-------|------|--------|---------|
| `ChatMsg` | DialogView.swift | id, sender, text, ts | DialogView |
| `ChatHistoryResponse` | DialogView.swift | messages: [ChatMsg] | DialogView.fetchHistory() |
| `DialogRequest` | DialogView.swift | text, sender | DialogView.send(), IntentEntryView.submitIntent() |
| `DialogResponse` | DialogView.swift | reply?, agreement_score?, models_responded?, elapsed_s?, ts? | DialogView.send() |
| `FeedItem` | TeamChatView.swift | id, type, sender, receiver, text, ts | TeamChatView |
| `FeedResponse` | TeamChatView.swift | items: [FeedItem], total: Int | TeamChatView.fetchFull/pollDelta |
| `UnifiedAgentDTO` | TeamChatView.swift | name, alive, pace, mode, billing_mode, T_day, dollar_day, floor_gap, lease_token, lease_expired, lease_expires_at?, office_status, pending_msgs, tasks_open, tasks_claimed, last_activity?, last_feed? | TeamChatView.fetchAgents() |
| `UnifiedStatusResponse` | TeamChatView.swift | _ts, agents: [String: UnifiedAgentDTO] | TeamChatView.fetchAgents() |
| `RadioAgentInfo` | TeamChatView.swift | name, alive, pace, mode, billingMode, tDay, dollarDay, floorGap, leaseToken, leaseExpired, officeStatus, pendingMsgs, tasksOpen, tasksClaimed, lastActivity?, lastFeed | TeamChatView agent sheet |
| `AgentStatus` | GovernorView.swift | name, alive, pace, forecast?, mode, billing_mode?, upper_rail_enabled?, T_day, dollar_day, budget_cap?, budget_remaining?, floor_expected?, floor_gap, hour?, hard_fail, office_status?, pending_msgs?, tasks_open?, tasks_claimed?, last_activity? | GovernorView |
| `GovernorUnifiedResponse` | GovernorView.swift | _ts, agents: [String: AgentStatus] | GovernorView.fetch() |
| `PulseQueueSummary` | PulseMonitorView.swift | total, counts: {}, active_by_priority: {}, stale_count, _updated? | PulseMonitorView |
| `PulseAgentDTO` | PulseMonitorView.swift | name, alive, pace, mode, billing_mode, T_day, dollar_day, floor_gap, lease_token, lease_expired, lease_expires_at?, office_status, pending_msgs, tasks_open, tasks_claimed, last_activity?, last_feed? | PulseMonitorView |
| `PulseUnifiedResponse` | PulseMonitorView.swift | _ts, agents: [String: PulseAgentDTO] | PulseMonitorView.fetchAgents() |
| `TaskItem` | TasksView.swift | id, title, priority, status, agent, claimed_by, tags: [] | TasksView |
| `TasksResponse` | TasksView.swift | tasks: [TaskItem] | TasksView.fetch() |
| `PilotCommand` | ScreenPilotView.swift | id, action, x?, y?, x2?, y2?, text?, ts | ScreenPilotView |
| `PilotCommandsResponse` | ScreenPilotView.swift | commands: [PilotCommand] | ScreenPilotView.pollCommands() |
| `IntentRoute` | RheaPreviewApp.swift | id, title, subtitle, seed, role, revealLevel, icon | IntentEntryView |

### Non-DTO Models

| Model | File | Type | Purpose |
|-------|------|------|---------|
| `RheaTheme` | Theme.swift | enum (namespace) | All app colors + semantic color functions |
| `GlassCard` | Theme.swift | ViewModifier | Frosted-glass card background |
| `AppConfig` | AppConfig.swift | enum (namespace) | URL defaults, simulator detection, stale migration |
| `ConnectionStatus` | SettingsView.swift | enum (nested) | .unknown / .checking / .ok / .failed(String) |

### DTO Duplication Note

Three views decode the **same** `/agents/status` endpoint with three separate DTOs:
- `UnifiedAgentDTO` (TeamChatView) -- 17 fields
- `PulseAgentDTO` (PulseMonitorView) -- 17 fields (identical to Unified)
- `AgentStatus` (GovernorView) -- 21 fields (superset, adds forecast, budget_cap, budget_remaining, floor_expected, upper_rail_enabled, hard_fail)

These should be consolidated into a single shared DTO.

---

## 5. Complete API Surface

### Endpoints Called

| Method | Path | Auth | Called From | Returns |
|--------|------|------|-------------|---------|
| GET | `/agents/status` | none | TeamChatView, GovernorView, PulseMonitorView | `{ _ts, agents: {name: AgentDTO} }` |
| POST | `/agents/wake/{AGENT}` | none | TeamChatView, GovernorView (AgentCard), PulseMonitorView | 200 OK |
| GET | `/feed?limit=100` | none | TeamChatView.fetchFull() | `{ items: [FeedItem], total }` |
| GET | `/feed?limit=20&since={ts}` | none | TeamChatView.pollDelta() | `{ items: [FeedItem], total }` |
| POST | `/feed/push` | none | TeamChatView.sendMessage(), GovernorView (ping), PulseMonitorView.markFlicker() | 200 OK |
| POST | `/office/send` | none | TeamChatView.sendOfficeMessage() | 200 OK |
| POST | `/dialog` | X-API-Key: dev-bypass | DialogView.send(), IntentEntryView.submitIntent() | `{ reply, agreement_score, models_responded, elapsed_s, ts }` |
| GET | `/chat?limit=50` | X-API-Key: dev-bypass | DialogView.fetchHistory() | `{ messages: [ChatMsg] }` |
| GET | `/tasks` | none | TasksView.fetch() | `{ tasks: [TaskItem] }` |
| POST | `/tasks?title=...&priority=...&agent=...&tags=...` | none | PulseMonitorView.createTraceTask() | 200 OK |
| GET | `/tasks/summary` | none | PulseMonitorView.fetchSummary() | `{ total, counts, active_by_priority, stale_count }` |
| GET | `/pilot/commands` | X-API-Key: dev-bypass | ScreenPilotView.pollCommands() | `{ commands: [PilotCommand] }` |
| POST | `/pilot/screenshot` | X-API-Key: dev-bypass, Content-Type: image/png | ScreenPilotView.captureAndSend() | 200 OK |
| GET | `/health` | none | SettingsView.testConnection() | 200 OK |
| GET | `{atlasBaseURL}/` | none | AtlasWebView (WKWebView load) | HTML page |

### API Base URL Strategy

- **Simulator**: `http://localhost:8400`
- **Device**: `https://rhea-tribunal-api-145767756165.europe-west1.run.app`
- **Atlas**: `http://localhost:3000` (always, no device override)
- Stale localhost/LAN URLs are auto-migrated to Cloud Run on device launch

### Polling Intervals

| View | Interval | Mechanism |
|------|----------|-----------|
| TeamChatView | 3s | Timer -> pollDelta() |
| PulseMonitorView | 5s | Timer -> refresh() (summary + agents) |
| DialogView | 5s | Timer -> fetchHistory() |
| ScreenPilotView | 1s | Timer -> pollCommands() |

---

## 6. Complete State Property Catalog

### @AppStorage (UserDefaults-persisted)

| Key | Type | Default | Used In |
|-----|------|---------|---------|
| `apiBaseURL` | String | localhost:8400 or Cloud Run | DialogView, TeamChatView, GovernorView, TasksView, PulseMonitorView, ScreenPilotView, SettingsView, IntentEntryView, AgentCard |
| `atlasBaseURL` | String | `http://localhost:3000` | AtlasView, SettingsView |
| `hasEnteredIntent` | Bool | false | RheaPreviewApp, IntentEntryView, SettingsView |
| `intentRevealLevel` | Int | 1 | RheaPreviewApp, IntentEntryView, SettingsView |
| `intentRole` | String | "biochemist" | IntentEntryView, SettingsView |
| `firstIntentText` | String | "" | IntentEntryView, SettingsView |
| `table_rex` | Bool | true | TeamChatView, PulseMonitorView, SettingsView |
| `table_orion` | Bool | true | TeamChatView, PulseMonitorView, SettingsView |
| `table_gpt` | Bool | false | TeamChatView, PulseMonitorView, SettingsView |
| `table_hyperion` | Bool | true | TeamChatView, PulseMonitorView, SettingsView |
| `table_gemini` | Bool | false | TeamChatView, PulseMonitorView, SettingsView |
| `table_shared` | Bool | false | TeamChatView, PulseMonitorView, SettingsView |
| `family_visibility_only` | Bool | false | TeamChatView, PulseMonitorView, SettingsView |
| `family_send_mode` | Bool | true | TeamChatView, SettingsView |
| `table_experiment_mode` | Bool | true | TeamChatView |
| `table_session_id` | String | "" | TeamChatView |
| `table_turn_counter` | Int | 0 | TeamChatView |

### @State (per-view ephemeral state)

| View | Property | Type | Purpose |
|------|----------|------|---------|
| **RheaPreviewApp** | selectedTab | Int | Current active tab |
| **IntentEntryView** | intentText | String | User-typed query |
| | isSending | Bool | Network request in flight |
| | errorText | String? | Error display |
| **DialogView** | messages | [ChatMsg] | Chat history |
| | inputText | String | Composer text |
| | isSending | Bool | Send in progress |
| | targetAgent | String | Selected agent target |
| | pollTimer | Timer? | Background poll handle |
| | lastMsgID | String | Dedup anchor |
| | agentResponse | String? | Inline response overlay |
| **TeamChatView** | items | [FeedItem] | Full radio feed |
| | activeSenders | Set<String> | Who spoke in last 5 min |
| | latestItem | FeedItem? | Most recent for flash |
| | pulse | Bool | ON AIR dot animation |
| | pollTimer | Timer? | 3s poll handle |
| | lastTS | String | Delta-poll watermark |
| | expandedIDs | Set<String> | Expanded message IDs |
| | filterAgent | String? | Agent filter |
| | composerText | String | Message input |
| | isSending | Bool | Send lock |
| | prevItemCount | Int | Change detection |
| | showBubbles | Bool | Console vs bubble mode |
| | showAgentSheet | Bool | Sheet presentation |
| | knownAgents | [RadioAgentInfo] | Agent roster |
| | wakingAgent | String? | Wake-in-progress ID |
| | activeTurnTag | String? | TABLE experiment turn tag |
| | activeTurnTargets | [String] | TABLE experiment targets |
| **GovernorView** | agents | [AgentStatus] | Decoded agent list |
| | loading | Bool | Loading spinner |
| | refreshCount | Int | Animation trigger |
| **TasksView** | tasks | [TaskItem] | Task list |
| | loading | Bool | Loading spinner |
| | filter | String | Active filter (all/open/...) |
| **PulseMonitorView** | summary | PulseQueueSummary? | Queue stats |
| | agents | [String: PulseAgentDTO] | Agent map |
| | loading | Bool | Loading spinner |
| | lastAction | String | Action result label |
| | pollTimer | Timer? | 5s poll handle |
| | flickerNote | String | Flicker note text |
| **ScreenPilotView** | isRecording | Bool | (unused -- see Unrealized) |
| | isPilotActive | Bool | Pilot mode toggle |
| | lastCommand | PilotCommand? | Last received command |
| | tapIndicator | CGPoint? | Tap overlay position |
| | statusText | String | Status label |
| | pollTimer | Timer? | 1s poll handle |
| **SettingsView** | draftAtlas | String | Unsaved atlas URL |
| | draftAPI | String | Unsaved API URL |
| | connectionStatus | ConnectionStatus | Health check result |
| **AgentCard** | appeared | Bool | Entrance animation |
| | actionInProgress | String? | Wake/Ping lock |
| **TaskCard** | appeared | Bool | Entrance animation |
| **ConsoleLine** | appeared | Bool | Fade-in animation |
| **BubbleLine** | appeared | Bool | Fade-in animation |

---

## 7. Navigation Map

### Primary Navigation

- **App launch** -> IntentEntryView (gate) OR MainTabShell (if intent set)
- **IntentEntryView "Start"** -> POST /dialog -> set hasEnteredIntent=true -> MainTabShell tab 0
- **IntentEntryView "Expert"** -> set revealLevel=3 -> MainTabShell tab 2
- **MainTabShell** -> TabView with 7 potential tabs (gated by revealLevel)

### Sheet Presentations

| Trigger | Sheet | Detents |
|---------|-------|---------|
| TeamChatView toolbar "person.3" button | agentSheet (agent roster + wake) | .medium, .large |

### Tab Gating (Progressive Disclosure)

| Level | Tabs Visible |
|-------|-------------|
| 1 (default) | Dialog, Team, Settings |
| 2 | + Governor, Tasks |
| 3 | + Atlas, Pulse |

---

## 8. Platform Guards

### #if os(iOS) / #else

| File | Line(s) | Guard | Purpose |
|------|---------|-------|---------|
| AtlasWebView.swift | 12-28 vs 29-43 | `#if os(iOS)` / `#else` | UIViewRepresentable vs NSViewRepresentable for WKWebView |
| TasksView.swift | 74-76 | `#if os(iOS)` | `.toolbarColorScheme(.dark, for: .navigationBar)` |
| TeamChatView.swift | 130-132 | `#if os(iOS)` | `UIApplication.shared.sendAction(resignFirstResponder)` keyboard dismiss |
| TeamChatView.swift | 162-164 | `#if os(iOS)` | `.toolbarColorScheme(.dark, for: .navigationBar)` |
| TeamChatView.swift | 518-519 | `#if os(iOS)` | `.toolbarColorScheme(.dark, for: .navigationBar)` in agent sheet |
| TeamChatView.swift | 611-613 | `#if os(iOS)` | `UINotificationFeedbackGenerator` on wake success |
| TeamChatView.swift | 657-659 | `#if os(iOS)` | `UIImpactFeedbackGenerator` on new feed items |
| PulseMonitorView.swift | 71-72 | `#if os(iOS)` | `.toolbarColorScheme(.dark, for: .navigationBar)` |
| GovernorView.swift | 64-65 | `#if os(iOS)` | `.toolbarColorScheme(.dark, for: .navigationBar)` |
| GovernorView.swift | 284-286 | `#if os(iOS)` | `UINotificationFeedbackGenerator` on action success |

### #if targetEnvironment(simulator) / #else

| File | Line(s) | Purpose |
|------|---------|---------|
| AppConfig.swift | 11-15 | Default API URL: localhost:8400 (sim) vs Cloud Run (device) |
| AppConfig.swift | 47-52 | Skip stale-URL migration on simulator |

---

## 9. Dependency Graph

### Direct Dependencies (Package.swift)

```
RheaPreview (iOS 17+)
  |
  +-- Pow 1.0.0+              (serg-alexv/Pow)          -- Animation effects
  +-- SwiftUIX 0.2.2+         (serg-alexv/SwiftUIX)     -- Extended SwiftUI APIs
  +-- ExyteChat 2.0.0+        (serg-alexv/Chat)         -- Chat UI framework
  +-- PopupView 3.0.0+        (serg-alexv/PopupView)    -- Toast/popup system
  +-- AnimatedTabBar 0.0.1+   (serg-alexv/AnimatedTabBar) -- Tab bar animations
  +-- FloatingButton 1.2.0+   (serg-alexv/FloatingButton) -- FAB menu
  +-- AlertKit 5.1.0+         (serg-alexv/AlertKit)     -- Native alert wrapper
  +-- Kingfisher (transitive)  (serg-alexv/Kingfisher)   -- Image loading/caching
```

### Actually Used in Source

| Package | Import Location | Usage |
|---------|----------------|-------|
| **Pow** | TasksView.swift, GovernorView.swift | `.changeEffect(.rise)`, `.changeEffect(.pulse)`, `.changeEffect(.shake)`, `.transition(.movingParts.pop)` |
| **Charts** | GovernorView.swift | `import Charts` (imported but NOT used in rendered views -- no Chart{} calls) |
| **WebKit** | AtlasWebView.swift | WKWebView for Atlas embed |
| **ReplayKit** | ScreenPilotView.swift | `import ReplayKit` (imported but NOT used -- no RPScreenRecorder calls) |

### NOT Used in Source (declared but zero imports)

- SwiftUIX
- ExyteChat
- PopupView
- AnimatedTabBar
- FloatingButton
- AlertKit
- Kingfisher

These are declared in Package.swift and the RheaPlusUI umbrella but have zero imports in the 11 source files.

### RheaPlusUI Umbrella (ios/rhea-plus-ui/)

Separate SPM library that `@_exported` re-exports all 8 packages. Not referenced by the main app's Package.swift -- it exists as a standalone reusable library definition.

### xcodegen Build (project.yml)

The App Store build via `ios/RheaApp/project.yml` only declares **Pow** as a dependency (not the full Package.swift dependency list). Sources point to `../RheaPreview.swiftpm/Sources`.

---

## 10. Unrealized Potential (Stubs, Partial, Unused)

### Fully Orphaned Views

| Feature | Status | Detail |
|---------|--------|--------|
| **ScreenPilotView** | Orphan | Complete view (234 lines) with pilot commands, screenshot capture, and tap overlay. NOT wired into any tab or navigation. Would need a tab entry or navigation link to activate. |

### Unused Imports

| Import | File | Status |
|--------|------|--------|
| `import Charts` | GovernorView.swift | Imported but no `Chart{}` view rendered. Likely planned for token/cost time-series charts. |
| `import ReplayKit` | ScreenPilotView.swift | Imported but `RPScreenRecorder` never used. `isRecording` @State exists but is never toggled. Screenshot uses UIGraphicsImageRenderer instead. |

### Unused Dependencies (7 of 8)

The following packages are declared in Package.swift but never imported in any source file:

- **SwiftUIX** -- Extended SwiftUI components (not yet adopted)
- **ExyteChat** -- Full chat UI framework (DialogView uses custom bubbles instead)
- **PopupView** -- Toast/popup library (no popup() calls)
- **AnimatedTabBar** -- Animated tab bar (standard TabView used instead)
- **FloatingButton** -- FAB menu (no floating buttons in any view)
- **AlertKit** -- Native alerts (no AlertKit calls)
- **Kingfisher** -- Image caching (no remote images loaded)

These represent a reserved UI toolkit for future features.

### Partial/Stubbed Features

| Feature | Evidence | Gap |
|---------|----------|-----|
| **Screen recording** | `@State private var isRecording = false` in ScreenPilotView, `import ReplayKit` | Toggle never connected, no RPScreenRecorder usage |
| **Budget remaining display** | `AgentStatus.budget_remaining` decoded | Never rendered in GovernorView UI |
| **Forecast display** | `AgentStatus.forecast` decoded | Never rendered |
| **Upper rail toggle** | `AgentStatus.upper_rail_enabled` decoded | Never rendered |
| **Floor expected** | `AgentStatus.floor_expected` decoded | Never rendered |
| **Swipe pilot command** | `PilotCommand` has `x2`, `y2` fields | `executeCommand()` only handles "tap" and "screenshot", not "swipe" or "type" |
| **Type pilot command** | `PilotCommand.text` field, action "type" | Not handled in executeCommand() switch |
| **prevItemCount** | `@State private var prevItemCount = 0` in TeamChatView | Set at declaration but never read or updated |
| **Task item agent field** | `TaskItem.agent` decoded | Displayed nowhere (only `claimed_by` shown) |
| **Investor intent route** | IntentRoute with id:"investor" defined | Routes to same /dialog endpoint, no specialized investor view |

### DTO Consolidation Opportunity

Three separate but near-identical DTOs decode `/agents/status`:
- `UnifiedAgentDTO` (TeamChatView) + `RadioAgentInfo` (mapped from it)
- `PulseAgentDTO` (PulseMonitorView) -- field-identical to UnifiedAgentDTO
- `AgentStatus` (GovernorView) -- superset with 4 extra fields

A single `AgentDTO` with optional fields would eliminate ~80 lines of duplicate struct definitions.

---

## 11. Build Configuration

### App Identity

| Property | Value |
|----------|-------|
| Bundle ID | `com.rhea.preview` |
| Display Name | Rhea |
| Marketing Version | 1.0 |
| Build Number | 7 |
| Team ID | 398XACWZ7G (TAIMLABS, OOO) |
| Min iOS | 17.0 |
| Swift | 5.9 |
| Signing | Automatic |

### Info.plist Highlights

- `NSAllowsLocalNetworking: true` -- permits localhost API calls on device
- All 4 orientations supported (portrait, landscape L/R, upside down)
- `UILaunchScreen: {}` -- system default launch screen

### Assets

- `AppIcon.appiconset/icon_1024.png` -- single 1024x1024 icon

---

## 12. Color System

```
RheaTheme
  .bg     = (0.06, 0.06, 0.10)    -- near-black background
  .card   = (0.10, 0.10, 0.16)    -- raised card surface
  .cardBorder = white @ 6%         -- subtle card edge
  .accent = (0.40, 0.85, 1.0)     -- cyan (Rex, active states)
  .green  = (0.30, 0.90, 0.50)    -- success, human messages
  .amber  = (1.0, 0.78, 0.20)     -- warnings, Gemini
  .red    = (1.0, 0.35, 0.35)     -- errors, P0, hard_fail

  Agent colors:
    rex     -> accent (cyan)
    orion   -> .purple
    gemini  -> amber
    human   -> green
    relay   -> .orange
    tribunal -> .cyan
    hyperion -> amber (GovernorView) / .mint (PulseMonitorView SeatToggle)
```

Note: Agent-to-color mapping is duplicated across TeamChatView, ConsoleLine, BubbleLine, DialogView, and GovernorView with minor inconsistencies (e.g., orion is `.purple` in TeamChat but `.green` in DialogView; hyperion is `.amber` in one and unhandled/default in another).

---

## 13. Summary Statistics

| Metric | Value |
|--------|-------|
| Swift source files | 11 |
| Total source lines | 3,194 |
| SwiftUI Views | 18 (11 primary + 7 subcomponents) |
| Data models (DTOs) | 16 |
| API endpoints | 14 distinct paths |
| @AppStorage keys | 17 |
| @State properties | 52 |
| External packages declared | 8 |
| External packages actually used | 2 (Pow, WebKit stdlib) |
| Platform guards (#if) | 10 |
| Orphaned views | 1 (ScreenPilotView) |
| Unused imports | 2 (Charts, ReplayKit) |
| Polling timers | 4 (1s, 3s, 5s, 5s) |
| Haptic feedback points | 3 |
