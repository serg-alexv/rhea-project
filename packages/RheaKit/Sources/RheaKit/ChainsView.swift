import SwiftUI

/// Unified chains + processes view.
/// - Chains tab: node-graph chain builder (was NodeEditorView)
/// - Procs tab: supervisor session manager (was ProcessesView)
public struct ChainsView: View {
    @State private var selectedTab = 0

    public init() {}

    public var body: some View {
        VStack(spacing: 0) {
            Picker("Section", selection: $selectedTab) {
                Text("Chains").tag(0)
                Text("Procs").tag(1)
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, 16)
            .padding(.top, 8)

            if selectedTab == 0 {
                NodeEditorView()
            } else {
                ProcessesView()
            }
        }
        .background(RheaTheme.bg)
    }
}
