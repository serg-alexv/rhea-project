// rhea-tray — macOS menu bar health monitor
// Reads ~/.rhea/health-status.json from the rhea-health daemon
// Shows green/yellow/red dot + dropdown with tracked processes
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

// MARK: — Tray controller

class HealthTray: NSObject {
    private var statusItem: NSStatusItem!
    private var timer: Timer?
    private let statusPath: String
    private let logPath: String
    private var lastStatus: HealthStatus?
    private var recentKills: [HealthEvent] = []

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

        // Show count if tracking
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

        // Status
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

            // Timestamp
            let ts = status.ts.prefix(19).replacingOccurrences(of: "T", with: " ")
            let tsItem = NSMenuItem(title: "Last scan: \(ts)", action: nil, keyEquivalent: "")
            tsItem.isEnabled = false
            menu.addItem(tsItem)
        } else {
            let item = NSMenuItem(title: "⏳ Waiting for daemon...", action: nil, keyEquivalent: "")
            item.isEnabled = false
            menu.addItem(item)
        }

        // Recent kills
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

        // Actions
        let openLog = NSMenuItem(title: "Open Health Log…", action: #selector(openLogFile), keyEquivalent: "l")
        openLog.target = self
        menu.addItem(openLog)

        let openStatus = NSMenuItem(title: "Open Status JSON…", action: #selector(openStatusFile), keyEquivalent: "s")
        openStatus.target = self
        menu.addItem(openStatus)

        menu.addItem(NSMenuItem.separator())

        let quit = NSMenuItem(title: "Quit Tray", action: #selector(quitApp), keyEquivalent: "q")
        quit.target = self
        menu.addItem(quit)

        statusItem.menu = menu
    }

    @objc private func openLogFile() {
        NSWorkspace.shared.open(URL(fileURLWithPath: logPath))
    }

    @objc private func openStatusFile() {
        NSWorkspace.shared.open(URL(fileURLWithPath: statusPath))
    }

    @objc private func quitApp() {
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
