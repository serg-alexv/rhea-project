import SwiftUI

public struct PlayRuntimeDebugView: View {
    @StateObject private var runtime = PlayRuntimeCore()
    @State private var autoScroll = true
    
    public init() {}
    
    public var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header: Status & Control
            header
            
            // Loaded Plugins (Scripts)
            if !runtime.loadedScripts.isEmpty {
                pluginStrip
            }
            
            // Execution Logs
            logSurface
            
            // Error Banner
            if let error = runtime.lastError {
                errorBanner(error)
            }
        }
        .padding()
        .background(Color(red: 0.05, green: 0.05, blue: 0.07))
        .onAppear {
            if runtime.status == .idle {
                runtime.boot()
            }
        }
    }
    
    // MARK: - Components
    
    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text("RHEA PLAY RUNTIME")
                    .font(.system(size: 14, weight: .black, design: .monospaced))
                    .foregroundStyle(RheaTheme.accent)
                
                HStack(spacing: 8) {
                    Circle()
                        .fill(statusColor)
                        .frame(width: 8, height: 8)
                    Text(runtime.status.rawValue.uppercased())
                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                        .foregroundStyle(statusColor)
                }
            }
            
            Spacer()
            
            Button(action: { runtime.boot() }) {
                HStack {
                    Image(systemName: runtime.status == .failed ? "arrow.clockwise" : "bolt.fill")
                    Text(runtime.status == .idle ? "BOOT" : "REBOOT")
                }
                .font(.system(size: 13, weight: .bold, design: .monospaced))
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Capsule().fill(statusColor.opacity(0.1)))
                .overlay(Capsule().stroke(statusColor, lineWidth: 1))
            }
        }
        .padding(.bottom, 4)
    }
    
    private var pluginStrip: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("LOADED PLUGINS")
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(.secondary)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 6) {
                    ForEach(runtime.loadedScripts, id: \.self) { script in
                        HStack(spacing: 4) {
                            Image(systemName: "puzzlepiece.fill")
                                .font(.system(size: 8))
                            Text(script)
                                .font(.system(size: 10, design: .monospaced))
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(RoundedRectangle(cornerRadius: 6).fill(Color.white.opacity(0.05)))
                        .overlay(RoundedRectangle(cornerRadius: 6).stroke(Color.white.opacity(0.1), lineWidth: 1))
                    }
                }
            }
        }
    }
    
    private var logSurface: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("EXECUTION LOGS")
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                Spacer()
                Button { autoScroll.toggle() } label: {
                    Image(systemName: autoScroll ? "chevron.down.circle.fill" : "chevron.down.circle")
                        .font(.system(size: 12))
                        .foregroundStyle(autoScroll ? RheaTheme.accent : .secondary)
                }
            }
            
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 4) {
                        if runtime.logs.isEmpty {
                            Text("No telemetry data yet.")
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundStyle(.secondary)
                                .padding()
                        } else {
                            ForEach(runtime.logs.indices, id: \.self) { idx in
                                logLine(runtime.logs[idx])
                                    .id(idx)
                            }
                        }
                    }
                    .padding(12)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(RoundedRectangle(cornerRadius: 12).fill(Color.black.opacity(0.4)))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.white.opacity(0.1), lineWidth: 1))
                .onChange(of: runtime.logs.count) { _ in
                    if autoScroll {
                        withAnimation { proxy.scrollTo(runtime.logs.count - 1, anchor: .bottom) }
                    }
                }
            }
        }
    }
    
    private func logLine(_ line: String) -> some View {
        let isError = line.contains("EXCEPTION") || line.contains("FATAL") || line.contains("failed")
        let isBoot = line.contains("BOOT")
        let isJS = line.contains("JS:")
        
        return Text(line)
            .font(.system(size: 11, design: .monospaced))
            .foregroundStyle(
                isError ? Color.red : 
                isBoot ? RheaTheme.accent :
                isJS ? RheaTheme.green.opacity(0.9) :
                .white.opacity(0.6)
            )
            .frame(maxWidth: .infinity, alignment: .leading)
    }
    
    private func errorBanner(_ msg: String) -> some View {
        HStack(spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.red)
            Text(msg)
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .lineLimit(2)
            Spacer()
        }
        .padding(10)
        .background(RoundedRectangle(cornerRadius: 10).fill(Color.red.opacity(0.1)))
        .overlay(RoundedRectangle(cornerRadius: 10).stroke(Color.red.opacity(0.3), lineWidth: 1))
    }
    
    private var statusColor: Color {
        switch runtime.status {
        case .idle: return .gray
        case .booting: return .orange
        case .running: return .green
        case .failed: return .red
        }
    }
}
