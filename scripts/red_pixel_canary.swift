import Cocoa
import Foundation

func argValue(_ key: String, _ defaultValue: Double) -> Double {
    if let idx = CommandLine.arguments.firstIndex(of: key), idx + 1 < CommandLine.arguments.count {
        return Double(CommandLine.arguments[idx + 1]) ?? defaultValue
    }
    return defaultValue
}

let xInset = argValue("--x", 2)
let yInset = argValue("--y", 2)
let size = max(1, argValue("--size", 2))

let app = NSApplication.shared
app.setActivationPolicy(.accessory)

guard let screen = NSScreen.main else {
    fputs("red_pixel_canary: no main screen\n", stderr)
    exit(1)
}

let screenFrame = screen.frame
let y = screenFrame.maxY - yInset - size
let rect = NSRect(x: xInset, y: y, width: size, height: size)

let window = NSWindow(
    contentRect: rect,
    styleMask: [.borderless],
    backing: .buffered,
    defer: false
)
window.level = .screenSaver
window.isOpaque = true
window.hasShadow = false
window.ignoresMouseEvents = true
window.collectionBehavior = [.canJoinAllSpaces, .stationary]
window.backgroundColor = NSColor.systemRed
window.makeKeyAndOrderFront(nil)
window.orderFrontRegardless()

var toggle = false
Timer.scheduledTimer(withTimeInterval: 0.35, repeats: true) { _ in
    toggle.toggle()
    window.backgroundColor = toggle ? NSColor.systemRed : NSColor(calibratedRed: 0.65, green: 0, blue: 0, alpha: 1)
}

app.run()
