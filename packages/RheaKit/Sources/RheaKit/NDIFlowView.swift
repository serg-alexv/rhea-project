import SwiftUI

public struct NDIFlowView: View {
    @State private var isAvailable = false

    public init() {}

    public var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "video.badge.waveform")
                .font(.system(size: 48))
                .foregroundStyle(RheaTheme.accent.opacity(0.4))

            Text("NDI FLOW")
                .font(.system(size: 18, weight: .bold, design: .monospaced))
                .foregroundStyle(.white)

            Text("Network Device Interface")
                .font(.system(size: 12, design: .monospaced))
                .foregroundStyle(.secondary)

            if isAvailable {
                Text("NDI source detected")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(RheaTheme.green)
            } else {
                VStack(spacing: 8) {
                    Text("Requires local NDI server")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(RheaTheme.amber)
                    Text("libndi v6.2.0 available at /usr/local/lib")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(RheaTheme.bg)
        .onAppear { checkNDI() }
    }

    private func checkNDI() {
        isAvailable = FileManager.default.fileExists(atPath: "/usr/local/lib/libndi.dylib")
    }
}
