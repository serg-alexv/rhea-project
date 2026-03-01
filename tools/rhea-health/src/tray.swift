// rhea-tray — macOS menu bar health monitor + NDI pulse + notification control
// Reads ~/.rhea/health-status.json from the rhea-health daemon
// Sends NDI health pulse via ndi_bridge.py
// Controls macOS Focus mode to silence notification noise
// Build: swiftc -framework Cocoa -o rhea-tray src/tray.swift

import Cocoa

// MARK: — Data model

struct WatchedProcess: Codable {
    let pid: Int
    let name: String
    let strikes: Int
    let cpu: Double
}

struct HealthStatus: Codable {
    let ts: String
    let tracking: Int
    let watched: [WatchedProcess]
}

struct HealthEvent: Codable {
    let ts: String
    let event: String
    let pid: Int
    let name: String
    let cpu: Double
    let action: String
}

// MARK: — NDI Pulse

class NDIPulse {
    private let projectRoot: String
    private var pulseTimer: Timer?
    private(set) var isActive = false
    private(set) var lastPulseOk = false

    init() {
        // Find project root from rhea-health binary location
        let home = NSHomeDirectory()
        // Try common locations
        let candidates = [
            "\(home)/rh.1",
            "\(home)/rh",
        ]
        projectRoot = candidates.first { FileManager.default.fileExists(atPath: "\($0)/src/ndi_bridge.py") } ?? "\(home)/rh.1"
    }

    func start() {
        guard !isActive else { return }
        isActive = true
        sendPulse() // immediate first pulse
        pulseTimer = Timer.scheduledTimer(withTimeInterval: 10.0, repeats: true) { [weak self] _ in
            self?.sendPulse()
        }
    }

    func stop() {
        pulseTimer?.invalidate()
        pulseTimer = nil
        isActive = false
    }

    private func sendPulse() {
        // Read current health state to determine pulse color
        let home = NSHomeDirectory()
        let statusPath = "\(home)/.rhea/health-status.json"
        var color = "green"

        if let data = FileManager.default.contents(atPath: statusPath),
           let status = try? JSONDecoder().decode(HealthStatus.self, from: data) {
            if status.watched.contains(where: { $0.strikes >= 2 }) {
                color = "red"
            } else if status.tracking > 0 {
                color = "yellow"
            }
        }

        // Call ndi_bridge.py to send a single pulse frame
        // We use a tiny Python script that sends one colored frame
        let script = """
        import sys; sys.path.insert(0, '\(projectRoot)/src')
        try:
            import ndi_bridge
            colors = {'green': (0,200,80,255), 'yellow': (255,200,0,255), 'red': (255,40,40,255)}
            c = colors.get('\(color)', (0,200,80,255))
            with ndi_bridge.NDISender('Rhea Health Pulse') as s:
                row = bytes(c) * 64
                frame = row * 64
                s.send_rgba(frame, 64, 64, fps=1)
            print('ok')
        except Exception as e:
            print(f'err:{e}')
        """

        DispatchQueue.global(qos: .utility).async { [weak self] in
            let task = Process()
            // Use pyenv python3 (3.11+) instead of system python3 (3.9)
            // System python3 fails on `str | None` type syntax
            let pythonCandidates = [
                "\(NSHomeDirectory())/.pyenv/versions/3.11.9/bin/python3",
                "/opt/homebrew/bin/python3",
                "/usr/local/bin/python3",
                "/usr/bin/python3",
            ]
            let pythonPath = pythonCandidates.first { FileManager.default.fileExists(atPath: $0) } ?? "/usr/bin/python3"
            task.executableURL = URL(fileURLWithPath: pythonPath)
            task.arguments = ["-c", script]
            let pipe = Pipe()
            task.standardOutput = pipe
            task.standardError = FileHandle.nullDevice

            do {
                try task.run()
                task.waitUntilExit()
                let data = pipe.fileHandleForReading.readDataToEndOfFile()
                let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                DispatchQueue.main.async {
                    self?.lastPulseOk = output == "ok"
                }
            } catch {
                DispatchQueue.main.async {
                    self?.lastPulseOk = false
                }
            }
        }
    }
}

// MARK: — Notification Control

class NotificationControl {
    private(set) var focusActive = false

    func checkFocusStatus() {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/defaults")
        task.arguments = ["read", "com.apple.controlcenter", "NSStatusItem Visible FocusModes"]
        let pipe = Pipe()
        task.standardOutput = pipe
        task.standardError = FileHandle.nullDevice
        do {
            try task.run()
            task.waitUntilExit()
        } catch {}
    }

    func toggleDND() {
        // Use AppleScript to toggle Focus/DND — most reliable method on modern macOS
        let script: String
        if focusActive {
            // Turn off DND
            script = """
            tell application "System Events"
                tell its application process "ControlCenter"
                    click menu bar item "Focus" of menu bar 1
                    delay 0.3
                    click checkbox 1 of group 1 of window "Control Center"
                end tell
            end tell
            """
        } else {
            // Use shortcuts — more reliable
            script = """
            do shell script "shortcuts run 'Do Not Disturb' 2>/dev/null || true"
            """
        }

        // Simpler approach: use `defaults` to write DND state
        // and `killall` to restart NC
        let dndScript = focusActive
            ? "defaults write com.apple.controlcenter 'NSStatusItem Visible FocusModes' -bool false"
            : "defaults write com.apple.controlcenter 'NSStatusItem Visible FocusModes' -bool true"

        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/bash")
        task.arguments = ["-c", dndScript]
        task.standardOutput = FileHandle.nullDevice
        task.standardError = FileHandle.nullDevice
        do {
            try task.run()
            task.waitUntilExit()
            focusActive.toggle()
        } catch {}
    }

    /// Silence a specific app's notifications via defaults
    func silenceApp(bundleId: String) {
        // Set notification flags to 0 (disabled) for this bundle
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/bin/bash")
        // Use sqlite to modify notification center DB directly
        let home = NSHomeDirectory()
        let cmd = """
        sqlite3 "\(home)/Library/Application Support/com.apple.notificationcenterui/db2/db" \
        "UPDATE record SET presented=0 WHERE app_id IN (SELECT app_id FROM app WHERE identifier='\(bundleId)');" 2>/dev/null
        """
        task.arguments = ["-c", cmd]
        task.standardOutput = FileHandle.nullDevice
        task.standardError = FileHandle.nullDevice
        do {
            try task.run()
            task.waitUntilExit()
        } catch {}
    }

    /// Clear all pending notifications
    func clearAll() {
        // Kill notification center to clear all banners
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/killall")
        task.arguments = ["NotificationCenter"]
        task.standardOutput = FileHandle.nullDevice
        task.standardError = FileHandle.nullDevice
        do {
            try task.run()
            task.waitUntilExit()
        } catch {}
    }
}

// MARK: — Tray controller

class HealthTray: NSObject {
    private var statusItem: NSStatusItem!
    private var timer: Timer?
    private let statusPath: String
    private let logPath: String
    private var lastStatus: HealthStatus?
    private var recentKills: [HealthEvent] = []
    let ndiPulse = NDIPulse()
    let notifControl = NotificationControl()

    override init() {
        let home = NSHomeDirectory()
        self.statusPath = "\(home)/.rhea/health-status.json"
        self.logPath = "\(home)/.rhea/health.log"
        super.init()
    }

    func setup() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

        if let button = statusItem.button {
            button.image = makeIcon(color: .systemGreen)
            button.toolTip = "Rhea Health Monitor"
        }

        // Auto-start NDI pulse
        ndiPulse.start()

        updateMenu()
        startPolling()
    }

    private func makeIcon(color: NSColor) -> NSImage {
        let size = NSSize(width: 18, height: 18)
        let img = NSImage(size: size, flipped: false) { rect in
            // Outer ring
            let ringRect = NSRect(x: 3, y: 3, width: 12, height: 12)
            let ring = NSBezierPath(ovalIn: ringRect)
            color.withAlphaComponent(0.3).setFill()
            ring.fill()

            // Inner dot
            let dotRect = NSRect(x: 5.5, y: 5.5, width: 7, height: 7)
            let dot = NSBezierPath(ovalIn: dotRect)
            color.setFill()
            dot.fill()

            return true
        }
        img.isTemplate = false
        return img
    }

    private func startPolling() {
        timer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            self?.refresh()
        }
        refresh()
    }

    private func refresh() {
        readStatus()
        readRecentKills()
        updateIcon()
        updateMenu()
    }

    private func readStatus() {
        guard let data = FileManager.default.contents(atPath: statusPath),
              let status = try? JSONDecoder().decode(HealthStatus.self, from: data) else {
            return
        }
        lastStatus = status
    }

    private func readRecentKills() {
        guard let data = FileManager.default.contents(atPath: logPath),
              let text = String(data: data, encoding: .utf8) else {
            recentKills = []
            return
        }

        let lines = text.components(separatedBy: "\n").suffix(50)
        recentKills = lines.compactMap { line in
            guard let data = line.data(using: .utf8),
                  let event = try? JSONDecoder().decode(HealthEvent.self, from: data),
                  event.event == "zombie_killed" else {
                return nil
            }
            return event
        }.suffix(5).reversed()
    }

    private func updateIcon() {
        guard let status = lastStatus, let button = statusItem.button else { return }

        let hasStrikes = status.watched.contains { $0.strikes >= 2 }
        let hasKills = !recentKills.isEmpty

        let color: NSColor
        if hasKills {
            color = .systemRed
        } else if hasStrikes || status.tracking > 0 {
            color = .systemYellow
        } else {
            color = .systemGreen
        }

        button.image = makeIcon(color: color)

        if status.tracking > 0 {
            button.title = " \(status.tracking)"
        } else {
            button.title = ""
        }
    }

    private func updateMenu() {
        let menu = NSMenu()

        // Header
        let header = NSMenuItem(title: "Rhea Health Monitor", action: nil, keyEquivalent: "")
        header.isEnabled = false
        if let font = NSFont.boldSystemFont(ofSize: 13) as NSFont? {
            header.attributedTitle = NSAttributedString(string: "Rhea Health Monitor",
                attributes: [.font: font])
        }
        menu.addItem(header)
        menu.addItem(NSMenuItem.separator())

        // --- Health Status ---
        if let status = lastStatus {
            if status.tracking == 0 {
                let item = NSMenuItem(title: "● All clear — no CPU hogs", action: nil, keyEquivalent: "")
                item.isEnabled = false
                menu.addItem(item)
            } else {
                let item = NSMenuItem(title: "⚠ Tracking \(status.tracking) process\(status.tracking == 1 ? "" : "es")", action: nil, keyEquivalent: "")
                item.isEnabled = false
                menu.addItem(item)

                for proc in status.watched {
                    let strike = String(repeating: "▮", count: proc.strikes) +
                                 String(repeating: "▯", count: max(0, 3 - proc.strikes))
                    let line = "  \(proc.name) (pid \(proc.pid)) — \(Int(proc.cpu))% CPU  \(strike)"
                    let pItem = NSMenuItem(title: line, action: nil, keyEquivalent: "")
                    pItem.isEnabled = false
                    if proc.strikes >= 2 {
                        pItem.attributedTitle = NSAttributedString(string: line,
                            attributes: [.foregroundColor: NSColor.systemOrange])
                    }
                    menu.addItem(pItem)
                }
            }

            let ts = status.ts.prefix(19).replacingOccurrences(of: "T", with: " ")
            let tsItem = NSMenuItem(title: "Last scan: \(ts)", action: nil, keyEquivalent: "")
            tsItem.isEnabled = false
            menu.addItem(tsItem)
        } else {
            let item = NSMenuItem(title: "⏳ Waiting for daemon...", action: nil, keyEquivalent: "")
            item.isEnabled = false
            menu.addItem(item)
        }

        // --- Recent Kills ---
        if !recentKills.isEmpty {
            menu.addItem(NSMenuItem.separator())
            let killHeader = NSMenuItem(title: "Recent Kills", action: nil, keyEquivalent: "")
            killHeader.isEnabled = false
            menu.addItem(killHeader)

            for kill in recentKills {
                let ts = kill.ts.prefix(19).replacingOccurrences(of: "T", with: " ")
                let line = "  ✕ \(kill.name) (pid \(kill.pid)) — \(Int(kill.cpu))% @ \(ts.suffix(8))"
                let kItem = NSMenuItem(title: line, action: nil, keyEquivalent: "")
                kItem.isEnabled = false
                kItem.attributedTitle = NSAttributedString(string: line,
                    attributes: [.foregroundColor: NSColor.systemRed])
                menu.addItem(kItem)
            }
        }

        menu.addItem(NSMenuItem.separator())

        // --- NDI Pulse ---
        let ndiHeader = NSMenuItem(title: "NDI Pulse", action: nil, keyEquivalent: "")
        ndiHeader.isEnabled = false
        if let font = NSFont.boldSystemFont(ofSize: 11) as NSFont? {
            ndiHeader.attributedTitle = NSAttributedString(string: "NDI Pulse",
                attributes: [.font: font])
        }
        menu.addItem(ndiHeader)

        let pulseStatus = ndiPulse.isActive
            ? (ndiPulse.lastPulseOk ? "● Broadcasting (10s interval)" : "● Active (NDI lib not found)")
            : "○ Stopped"
        let pulseItem = NSMenuItem(title: "  \(pulseStatus)", action: nil, keyEquivalent: "")
        pulseItem.isEnabled = false
        menu.addItem(pulseItem)

        let togglePulse = NSMenuItem(
            title: ndiPulse.isActive ? "  Stop NDI Pulse" : "  Start NDI Pulse",
            action: #selector(toggleNDIPulse),
            keyEquivalent: "n"
        )
        togglePulse.target = self
        menu.addItem(togglePulse)

        menu.addItem(NSMenuItem.separator())

        // --- Notification Control ---
        let notifHeader = NSMenuItem(title: "Notifications", action: nil, keyEquivalent: "")
        notifHeader.isEnabled = false
        if let font = NSFont.boldSystemFont(ofSize: 11) as NSFont? {
            notifHeader.attributedTitle = NSAttributedString(string: "Notifications",
                attributes: [.font: font])
        }
        menu.addItem(notifHeader)

        let clearNotifs = NSMenuItem(title: "  Clear All Notifications", action: #selector(clearNotifications), keyEquivalent: "c")
        clearNotifs.target = self
        menu.addItem(clearNotifs)

        let silenceXcode = NSMenuItem(title: "  Silence Xcode", action: #selector(silenceXcodeNotifs), keyEquivalent: "")
        silenceXcode.target = self
        menu.addItem(silenceXcode)

        let silenceChrome = NSMenuItem(title: "  Silence Chrome", action: #selector(silenceChromeNotifs), keyEquivalent: "")
        silenceChrome.target = self
        menu.addItem(silenceChrome)

        let silenceMail = NSMenuItem(title: "  Silence Mail", action: #selector(silenceMailNotifs), keyEquivalent: "")
        silenceMail.target = self
        menu.addItem(silenceMail)

        menu.addItem(NSMenuItem.separator())

        // --- Files ---
        let openLog = NSMenuItem(title: "Open Health Log…", action: #selector(openLogFile), keyEquivalent: "l")
        openLog.target = self
        menu.addItem(openLog)

        menu.addItem(NSMenuItem.separator())

        let quit = NSMenuItem(title: "Quit Tray", action: #selector(quitApp), keyEquivalent: "q")
        quit.target = self
        menu.addItem(quit)

        statusItem.menu = menu
    }

    // MARK: — Actions

    @objc private func toggleNDIPulse() {
        if ndiPulse.isActive {
            ndiPulse.stop()
        } else {
            ndiPulse.start()
        }
        updateMenu()
    }

    @objc private func clearNotifications() {
        notifControl.clearAll()
    }

    @objc private func silenceXcodeNotifs() {
        notifControl.silenceApp(bundleId: "com.apple.dt.Xcode")
    }

    @objc private func silenceChromeNotifs() {
        notifControl.silenceApp(bundleId: "com.google.Chrome")
    }

    @objc private func silenceMailNotifs() {
        notifControl.silenceApp(bundleId: "com.apple.mail")
    }

    @objc private func openLogFile() {
        NSWorkspace.shared.open(URL(fileURLWithPath: logPath))
    }

    @objc private func quitApp() {
        ndiPulse.stop()
        NSApplication.shared.terminate(nil)
    }
}

// MARK: — App delegate

class AppDelegate: NSObject, NSApplicationDelegate {
    let tray = HealthTray()

    func applicationDidFinishLaunching(_ notification: Notification) {
        tray.setup()
    }
}

// MARK: — Main

let app = NSApplication.shared
app.setActivationPolicy(.accessory) // no dock icon
let delegate = AppDelegate()
app.delegate = delegate
app.run()
