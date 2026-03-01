import SwiftUI
import ReplayKit
import RheaKit

// MARK: - API Models

struct PilotCommand: Codable, Identifiable {
    let id: String
    let action: String  // "tap", "swipe", "type", "screenshot"
    let x: Double?
    let y: Double?
    let x2: Double?
    let y2: Double?
    let text: String?
    let ts: String
}

struct PilotCommandsResponse: Codable {
    let commands: [PilotCommand]
}

// MARK: - Screen Pilot View

struct ScreenPilotView: View {
    @State private var isRecording = false
    @State private var isPilotActive = false
    @State private var lastCommand: PilotCommand? = nil
    @State private var tapIndicator: CGPoint? = nil
    @State private var statusText = "Pilot: OFF"
    @State private var pollTimer: Timer? = nil
    @AppStorage("apiBaseURL") private var apiBaseURL = AppConfig.defaultAPIBaseURL

    var body: some View {
        ZStack {
            // Main content
            VStack(spacing: 20) {
                // Status header
                HStack {
                    Circle()
                        .fill(isPilotActive ? Color.green : Color.red)
                        .frame(width: 10, height: 10)
                    Text(statusText)
                        .font(.system(size: 13, weight: .semibold, design: .monospaced))
                        .foregroundColor(.white)
                    Spacer()
                }
                .padding(.horizontal)

                // Controls
                HStack(spacing: 16) {
                    Button(action: togglePilot) {
                        HStack {
                            Image(systemName: isPilotActive ? "stop.fill" : "play.fill")
                            Text(isPilotActive ? "Stop Pilot" : "Start Pilot")
                        }
                        .font(.system(size: 14, weight: .bold, design: .monospaced))
                        .foregroundColor(.white)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(
                            Capsule().fill(isPilotActive ? Color.red.opacity(0.3) : Color.green.opacity(0.3))
                                .overlay(Capsule().stroke(isPilotActive ? Color.red : Color.green, lineWidth: 1))
                        )
                    }

                    Button(action: captureAndSend) {
                        HStack {
                            Image(systemName: "camera.fill")
                            Text("Capture")
                        }
                        .font(.system(size: 14, weight: .bold, design: .monospaced))
                        .foregroundColor(.white)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(
                            Capsule().fill(RheaTheme.accent.opacity(0.3))
                                .overlay(Capsule().stroke(RheaTheme.accent, lineWidth: 1))
                        )
                    }
                }

                // Command log
                if let cmd = lastCommand {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Last command:")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        Text("\(cmd.action) @ (\(Int(cmd.x ?? 0)), \(Int(cmd.y ?? 0)))")
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundColor(RheaTheme.green)
                        if let text = cmd.text {
                            Text("text: \(text)")
                                .font(.system(size: 12, design: .monospaced))
                                .foregroundColor(.white.opacity(0.7))
                        }
                    }
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(RoundedRectangle(cornerRadius: 10).fill(RheaTheme.card))
                    .padding(.horizontal)
                }

                Spacer()

                // Instructions
                Text("Pilot mode: Rex sends tap coordinates via API.\nThis view captures screenshots and shows tap targets.")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding()
            }
            .padding(.top)

            // Tap indicator overlay
            if let point = tapIndicator {
                Circle()
                    .stroke(Color.orange, lineWidth: 3)
                    .frame(width: 44, height: 44)
                    .position(point)
                    .animation(.easeOut(duration: 0.3), value: point)
                    .allowsHitTesting(false)

                Circle()
                    .fill(Color.orange.opacity(0.3))
                    .frame(width: 44, height: 44)
                    .position(point)
                    .allowsHitTesting(false)
            }
        }
        .background(RheaTheme.bg)
        .navigationTitle("Pilot")
        .onDisappear { stopPilot() }
    }

    // MARK: - Pilot Control

    private func togglePilot() {
        if isPilotActive {
            stopPilot()
        } else {
            startPilot()
        }
    }

    private func startPilot() {
        isPilotActive = true
        statusText = "Pilot: ACTIVE — polling for commands"
        pollTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            pollCommands()
        }
    }

    private func stopPilot() {
        isPilotActive = false
        statusText = "Pilot: OFF"
        pollTimer?.invalidate()
        pollTimer = nil
        tapIndicator = nil
    }

    // MARK: - Networking

    private func pollCommands() {
        guard let url = URL(string: "\(apiBaseURL)/pilot/commands") else { return }
        var req = URLRequest(url: url)
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        URLSession.shared.dataTask(with: req) { data, _, _ in
            guard let data = data,
                  let resp = try? JSONDecoder().decode(PilotCommandsResponse.self, from: data),
                  let cmd = resp.commands.first else { return }
            DispatchQueue.main.async {
                lastCommand = cmd
                executeCommand(cmd)
            }
        }.resume()
    }

    private func executeCommand(_ cmd: PilotCommand) {
        switch cmd.action {
        case "tap":
            if let x = cmd.x, let y = cmd.y {
                tapIndicator = CGPoint(x: x, y: y)
                statusText = "TAP → (\(Int(x)), \(Int(y)))"
                // Auto-hide after 2s
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    if tapIndicator == CGPoint(x: x, y: y) {
                        tapIndicator = nil
                    }
                }
            }
        case "screenshot":
            captureAndSend()
        default:
            statusText = "Unknown: \(cmd.action)"
        }
    }

    private func captureAndSend() {
        statusText = "Capturing screen..."
        // Take a snapshot of the current window
        guard let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
              let window = windowScene.windows.first else {
            statusText = "No window available"
            return
        }

        let renderer = UIGraphicsImageRenderer(bounds: window.bounds)
        let image = renderer.image { ctx in
            window.drawHierarchy(in: window.bounds, afterScreenUpdates: true)
        }

        guard let pngData = image.pngData() else {
            statusText = "PNG encode failed"
            return
        }

        // Upload to server
        guard let url = URL(string: "\(apiBaseURL)/pilot/screenshot") else { return }
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("image/png", forHTTPHeaderField: "Content-Type")
        req.setValue("dev-bypass", forHTTPHeaderField: "X-API-Key")
        req.httpBody = pngData

        URLSession.shared.dataTask(with: req) { _, response, error in
            DispatchQueue.main.async {
                if let http = response as? HTTPURLResponse, http.statusCode < 300 {
                    statusText = "Screenshot sent (\(pngData.count / 1024)KB)"
                } else {
                    statusText = "Upload failed: \(error?.localizedDescription ?? "?")"
                }
            }
        }.resume()
    }
}
