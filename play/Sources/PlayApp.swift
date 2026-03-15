import SwiftUI

@main
struct RheaPlayApp: App {
    @StateObject private var runtime = PlayRuntimeCore()

    var body: some Scene {
        WindowGroup("Rhea Play (Core)") {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("STATUS:")
                        .font(.caption.bold())
                    Text(runtime.status.rawValue.uppercased())
                        .foregroundColor(runtime.status == .failed ? .red : .green)
                    Spacer()
                    Button("BOOT") {
                        runtime.boot()
                    }
                    .keyboardShortcut("r", modifiers: .command)
                }
                .font(.system(.body, design: .monospaced))
                
                Divider()
                
                ScrollView {
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(runtime.logs, id: \.self) { log in
                            Text(log)
                                .font(.system(size: 11, design: .monospaced))
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .background(Color.black.opacity(0.05))
            }
            .padding()
            .frame(minWidth: 400, minHeight: 300)
            .onAppear {
                runtime.boot()
            }
        }
    }
}
