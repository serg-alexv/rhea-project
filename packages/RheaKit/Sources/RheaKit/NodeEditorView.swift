import SwiftUI

// MARK: - Node Type

public enum NodeType: String, CaseIterable, Codable {
    case input
    case tribunal
    case sceptic
    case filter
    case proof
    case output

    var label: String {
        switch self {
        case .input:    return "Input"
        case .tribunal: return "Tribunal"
        case .sceptic:  return "Sceptic"
        case .filter:   return "Filter"
        case .proof:    return "Proof"
        case .output:   return "Output"
        }
    }

    var icon: String {
        switch self {
        case .input:    return "text.cursor"
        case .tribunal: return "person.3.fill"
        case .sceptic:  return "exclamationmark.shield.fill"
        case .filter:   return "line.3.horizontal.decrease"
        case .proof:    return "checkmark.seal.fill"
        case .output:   return "doc.text.fill"
        }
    }

    var color: Color {
        switch self {
        case .input:    return RheaTheme.green
        case .tribunal: return RheaTheme.accent
        case .sceptic:  return RheaTheme.red
        case .filter:   return RheaTheme.amber
        case .proof:    return .purple
        case .output:   return .white
        }
    }

    var hasInputPort: Bool {
        self != .input
    }

    var hasOutputPort: Bool {
        self != .output
    }

    var defaultConfig: [String: String] {
        switch self {
        case .input:    return ["claim": ""]
        case .tribunal: return ["models": "3", "tier": "cheap"]
        case .sceptic:  return ["intensity": "medium"]
        case .filter:   return ["threshold": "70"]
        case .proof:    return ["tag": "gem"]
        case .output:   return [:]
        }
    }
}

// MARK: - Pipeline Node

public struct PipelineNode: Identifiable, Codable {
    public let id: UUID
    public var type: NodeType
    public var position: CGPoint
    public var connections: [UUID]
    public var config: [String: String]
    public var resultText: String?

    public init(type: NodeType, position: CGPoint) {
        self.id = UUID()
        self.type = type
        self.position = position
        self.connections = []
        self.config = type.defaultConfig
        self.resultText = nil
    }

    enum CodingKeys: String, CodingKey {
        case id, type, position, connections, config, resultText
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(UUID.self, forKey: .id)
        type = try c.decode(NodeType.self, forKey: .type)
        let pos = try c.decode([Double].self, forKey: .position)
        position = CGPoint(x: pos[0], y: pos[1])
        connections = try c.decode([UUID].self, forKey: .connections)
        config = try c.decode([String: String].self, forKey: .config)
        resultText = try c.decodeIfPresent(String.self, forKey: .resultText)
    }

    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(id, forKey: .id)
        try c.encode(type, forKey: .type)
        try c.encode([position.x, position.y], forKey: .position)
        try c.encode(connections, forKey: .connections)
        try c.encode(config, forKey: .config)
        try c.encodeIfPresent(resultText, forKey: .resultText)
    }
}

// MARK: - NodeEditorView

public struct NodeEditorView: View {
    @State private var nodes: [PipelineNode] = []
    @State private var selectedNodeId: UUID? = nil
    @State private var canvasOffset: CGSize = .zero
    @State private var canvasScale: CGFloat = 1.0
    @State private var dragCanvasStart: CGSize = .zero
    @State private var connectingFrom: UUID? = nil
    @State private var connectingEnd: CGPoint = .zero
    @State private var running = false
    @State private var runError: String? = nil
    @State private var showConfigPanel = false

    private let nodeWidth: CGFloat = 120
    private let nodeHeight: CGFloat = 80
    private let portRadius: CGFloat = 6

    public init() {}

    // MARK: - Body

    public var body: some View {
        ZStack(alignment: .bottom) {
            // Canvas background
            canvasLayer

            // Config panel overlay
            if showConfigPanel, let sid = selectedNodeId,
               let idx = nodes.firstIndex(where: { $0.id == sid }) {
                configPanelOverlay(nodeIndex: idx)
            }

            // Bottom toolbar
            bottomToolbar
        }
        .background(RheaTheme.bg)
        .preferredColorScheme(.dark)
    }

    // MARK: - Canvas

    private var canvasLayer: some View {
        GeometryReader { geo in
            ZStack {
                // Grid background
                gridPattern(size: geo.size)
                    .offset(canvasOffset)
                    .scaleEffect(canvasScale)

                // Connections
                connectionsLayer
                    .offset(canvasOffset)
                    .scaleEffect(canvasScale, anchor: .zero)

                // Active connection line (while dragging)
                if connectingFrom != nil {
                    activeConnectionLine
                        .offset(canvasOffset)
                        .scaleEffect(canvasScale, anchor: .zero)
                }

                // Nodes
                nodesLayer
                    .offset(canvasOffset)
                    .scaleEffect(canvasScale, anchor: .zero)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .contentShape(Rectangle())
            .gesture(canvasDragGesture)
            .gesture(canvasMagnifyGesture)
            .onTapGesture {
                withAnimation(.easeOut(duration: 0.2)) {
                    selectedNodeId = nil
                    showConfigPanel = false
                }
            }
        }
        .padding(.bottom, 60)
    }

    // MARK: - Grid Pattern

    private func gridPattern(size: CGSize) -> some View {
        Canvas { context, canvasSize in
            let spacing: CGFloat = 30
            let dotSize: CGFloat = 1.5
            let cols = Int(canvasSize.width * 2 / spacing) + 1
            let rows = Int(canvasSize.height * 2 / spacing) + 1
            let offsetX = canvasSize.width / 2
            let offsetY = canvasSize.height / 2
            for col in -cols/2...cols/2 {
                for row in -rows/2...rows/2 {
                    let x = CGFloat(col) * spacing + offsetX
                    let y = CGFloat(row) * spacing + offsetY
                    let rect = CGRect(
                        x: x - dotSize / 2,
                        y: y - dotSize / 2,
                        width: dotSize,
                        height: dotSize
                    )
                    context.fill(
                        Path(ellipseIn: rect),
                        with: .color(.white.opacity(0.06))
                    )
                }
            }
        }
        .allowsHitTesting(false)
    }

    // MARK: - Connections Layer

    private var connectionsLayer: some View {
        Canvas { context, _ in
            for node in nodes {
                let fromCenter = CGPoint(
                    x: node.position.x + nodeWidth,
                    y: node.position.y + nodeHeight / 2
                )
                for targetId in node.connections {
                    if let target = nodes.first(where: { $0.id == targetId }) {
                        let toCenter = CGPoint(
                            x: target.position.x,
                            y: target.position.y + nodeHeight / 2
                        )
                        let path = bezierConnection(from: fromCenter, to: toCenter)
                        context.stroke(
                            path,
                            with: .linearGradient(
                                Gradient(colors: [
                                    node.type.color.opacity(0.7),
                                    target.type.color.opacity(0.7)
                                ]),
                                startPoint: fromCenter,
                                endPoint: toCenter
                            ),
                            lineWidth: 2.5
                        )
                    }
                }
            }
        }
        .allowsHitTesting(false)
    }

    // MARK: - Active Connection Line

    private var activeConnectionLine: some View {
        Canvas { context, _ in
            guard let fromId = connectingFrom,
                  let fromNode = nodes.first(where: { $0.id == fromId }) else { return }
            let fromCenter = CGPoint(
                x: fromNode.position.x + nodeWidth,
                y: fromNode.position.y + nodeHeight / 2
            )
            let toPoint = canvasToLocal(connectingEnd)
            let path = bezierConnection(from: fromCenter, to: toPoint)
            context.stroke(
                path,
                with: .color(fromNode.type.color.opacity(0.5)),
                style: StrokeStyle(lineWidth: 2, dash: [6, 4])
            )
        }
        .allowsHitTesting(false)
    }

    // MARK: - Nodes Layer

    private var nodesLayer: some View {
        ForEach(Array(nodes.enumerated()), id: \.element.id) { index, node in
            nodeView(node: node, index: index)
                .position(
                    x: node.position.x + nodeWidth / 2,
                    y: node.position.y + nodeHeight / 2
                )
        }
    }

    // MARK: - Single Node View

    private func nodeView(node: PipelineNode, index: Int) -> some View {
        let isSelected = selectedNodeId == node.id

        return ZStack {
            // Node body
            RoundedRectangle(cornerRadius: 12)
                .fill(RheaTheme.card)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(
                            isSelected ? node.type.color : RheaTheme.cardBorder,
                            lineWidth: isSelected ? 2 : 1
                        )
                )
                .shadow(
                    color: isSelected ? node.type.color.opacity(0.3) : .clear,
                    radius: 8
                )
                .frame(width: nodeWidth, height: nodeHeight)

            // Content
            VStack(spacing: 4) {
                Image(systemName: node.type.icon)
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(node.type.color)
                Text(node.type.label)
                    .font(.system(size: 10, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)
                // Brief status
                if let result = node.resultText {
                    Text(result.prefix(20) + (result.count > 20 ? "..." : ""))
                        .font(.system(size: 8, design: .monospaced))
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                } else {
                    configSummary(node)
                }
            }

            // Input port (left)
            if node.type.hasInputPort {
                Circle()
                    .fill(RheaTheme.card)
                    .overlay(Circle().stroke(node.type.color.opacity(0.6), lineWidth: 1.5))
                    .frame(width: portRadius * 2, height: portRadius * 2)
                    .offset(x: -nodeWidth / 2, y: 0)
            }

            // Output port (right)
            if node.type.hasOutputPort {
                Circle()
                    .fill(node.type.color.opacity(0.8))
                    .frame(width: portRadius * 2, height: portRadius * 2)
                    .offset(x: nodeWidth / 2, y: 0)
                    .gesture(outputPortDrag(nodeId: node.id))
            }
        }
        .gesture(nodeDragGesture(index: index))
        .onTapGesture {
            withAnimation(.easeOut(duration: 0.2)) {
                if selectedNodeId == node.id {
                    showConfigPanel.toggle()
                } else {
                    selectedNodeId = node.id
                    showConfigPanel = true
                }
            }
        }
    }

    // MARK: - Config Summary

    @ViewBuilder
    private func configSummary(_ node: PipelineNode) -> some View {
        switch node.type {
        case .input:
            let claim = node.config["claim"] ?? ""
            Text(claim.isEmpty ? "tap to edit" : String(claim.prefix(16)))
                .font(.system(size: 8, design: .monospaced))
                .foregroundStyle(.secondary)
                .lineLimit(1)
        case .tribunal:
            Text("\(node.config["models"] ?? "3") models")
                .font(.system(size: 8, design: .monospaced))
                .foregroundStyle(.secondary)
        case .sceptic:
            Text(node.config["intensity"] ?? "medium")
                .font(.system(size: 8, design: .monospaced))
                .foregroundStyle(.secondary)
        case .filter:
            Text("\(node.config["threshold"] ?? "70")%")
                .font(.system(size: 8, design: .monospaced))
                .foregroundStyle(.secondary)
        case .proof:
            Text("#\(node.config["tag"] ?? "gem")")
                .font(.system(size: 8, design: .monospaced))
                .foregroundStyle(.secondary)
        case .output:
            Text("result")
                .font(.system(size: 8, design: .monospaced))
                .foregroundStyle(.secondary)
        }
    }

    // MARK: - Config Panel

    private func configPanelOverlay(nodeIndex: Int) -> some View {
        VStack(spacing: 0) {
            Spacer()

            VStack(alignment: .leading, spacing: 12) {
                // Header
                HStack {
                    Image(systemName: nodes[nodeIndex].type.icon)
                        .foregroundStyle(nodes[nodeIndex].type.color)
                    Text(nodes[nodeIndex].type.label.uppercased())
                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                        .foregroundStyle(nodes[nodeIndex].type.color)
                    Spacer()
                    Button {
                        let idToRemove = nodes[nodeIndex].id
                        withAnimation(.easeOut(duration: 0.2)) {
                            // Remove connections pointing to this node
                            for i in nodes.indices {
                                nodes[i].connections.removeAll { $0 == idToRemove }
                            }
                            nodes.remove(at: nodeIndex)
                            selectedNodeId = nil
                            showConfigPanel = false
                        }
                    } label: {
                        Image(systemName: "trash")
                            .font(.system(size: 12))
                            .foregroundStyle(RheaTheme.red)
                    }
                    .buttonStyle(.plain)
                    Button {
                        withAnimation(.easeOut(duration: 0.2)) {
                            showConfigPanel = false
                        }
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 16))
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }

                Divider().overlay(RheaTheme.cardBorder)

                configFields(nodeIndex: nodeIndex)

                // Connections info
                if !nodes[nodeIndex].connections.isEmpty {
                    HStack(spacing: 4) {
                        Image(systemName: "arrow.right.circle")
                            .font(.system(size: 10))
                            .foregroundStyle(.secondary)
                        Text("Connected to \(nodes[nodeIndex].connections.count) node(s)")
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(.secondary)
                        Spacer()
                        Button {
                            withAnimation(.easeOut(duration: 0.2)) {
                                nodes[nodeIndex].connections.removeAll()
                            }
                        } label: {
                            Text("Clear")
                                .font(.system(size: 10, weight: .medium, design: .monospaced))
                                .foregroundStyle(RheaTheme.red)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .glassCard()
            .padding(.horizontal, 12)
            .padding(.bottom, 68)
        }
        .transition(.move(edge: .bottom).combined(with: .opacity))
    }

    @ViewBuilder
    private func configFields(nodeIndex: Int) -> some View {
        let nodeType = nodes[nodeIndex].type

        switch nodeType {
        case .input:
            VStack(alignment: .leading, spacing: 4) {
                Text("CLAIM")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                TextField("Enter claim to verify...", text: binding(for: nodeIndex, key: "claim"), axis: .vertical)
                    .textFieldStyle(.plain)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundStyle(.white)
                    .lineLimit(2...5)
                    .padding(8)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(.white.opacity(0.04))
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(RheaTheme.green.opacity(0.2), lineWidth: 1))
                    )
            }

        case .tribunal:
            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("MODELS")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    HStack(spacing: 8) {
                        ForEach([3, 5, 7], id: \.self) { count in
                            Button {
                                nodes[nodeIndex].config["models"] = "\(count)"
                            } label: {
                                Text("\(count)")
                                    .font(.system(size: 13, weight: .bold, design: .monospaced))
                                    .foregroundStyle(
                                        nodes[nodeIndex].config["models"] == "\(count)"
                                            ? .white : .secondary
                                    )
                                    .frame(width: 32, height: 28)
                                    .background(
                                        RoundedRectangle(cornerRadius: 6)
                                            .fill(
                                                nodes[nodeIndex].config["models"] == "\(count)"
                                                    ? RheaTheme.accent.opacity(0.3)
                                                    : .white.opacity(0.04)
                                            )
                                    )
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 6)
                                            .stroke(
                                                nodes[nodeIndex].config["models"] == "\(count)"
                                                    ? RheaTheme.accent.opacity(0.5) : .clear,
                                                lineWidth: 1
                                            )
                                    )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                VStack(alignment: .leading, spacing: 4) {
                    Text("TIER")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    HStack(spacing: 6) {
                        ForEach(["cheap", "mid", "top"], id: \.self) { tier in
                            Button {
                                nodes[nodeIndex].config["tier"] = tier
                            } label: {
                                Text(tier)
                                    .font(.system(size: 10, weight: .medium, design: .monospaced))
                                    .foregroundStyle(
                                        nodes[nodeIndex].config["tier"] == tier
                                            ? .white : .secondary
                                    )
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 5)
                                    .background(
                                        RoundedRectangle(cornerRadius: 6)
                                            .fill(
                                                nodes[nodeIndex].config["tier"] == tier
                                                    ? RheaTheme.accent.opacity(0.2)
                                                    : .white.opacity(0.04)
                                            )
                                    )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }

        case .sceptic:
            VStack(alignment: .leading, spacing: 4) {
                Text("INTENSITY")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                HStack(spacing: 8) {
                    ForEach(["low", "medium", "high"], id: \.self) { level in
                        Button {
                            nodes[nodeIndex].config["intensity"] = level
                        } label: {
                            Text(level)
                                .font(.system(size: 11, weight: .medium, design: .monospaced))
                                .foregroundStyle(
                                    nodes[nodeIndex].config["intensity"] == level
                                        ? .white : .secondary
                                )
                                .padding(.horizontal, 10)
                                .padding(.vertical, 6)
                                .background(
                                    RoundedRectangle(cornerRadius: 6)
                                        .fill(
                                            nodes[nodeIndex].config["intensity"] == level
                                                ? RheaTheme.red.opacity(0.3)
                                                : .white.opacity(0.04)
                                        )
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 6)
                                        .stroke(
                                            nodes[nodeIndex].config["intensity"] == level
                                                ? RheaTheme.red.opacity(0.4) : .clear,
                                            lineWidth: 1
                                        )
                                )
                        }
                        .buttonStyle(.plain)
                    }
                }
            }

        case .filter:
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("THRESHOLD")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text("\(nodes[nodeIndex].config["threshold"] ?? "70")%")
                        .font(.system(size: 16, weight: .bold, design: .rounded))
                        .foregroundStyle(RheaTheme.amber)
                }
                Slider(
                    value: thresholdBinding(nodeIndex: nodeIndex),
                    in: 0...100,
                    step: 5
                )
                .tint(RheaTheme.amber)
            }

        case .proof:
            VStack(alignment: .leading, spacing: 4) {
                Text("TAG")
                    .font(.system(size: 9, weight: .bold, design: .monospaced))
                    .foregroundStyle(.secondary)
                TextField("gem", text: binding(for: nodeIndex, key: "tag"))
                    .textFieldStyle(.plain)
                    .font(.system(size: 13, design: .monospaced))
                    .foregroundStyle(.white)
                    .padding(8)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(.white.opacity(0.04))
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.purple.opacity(0.2), lineWidth: 1))
                    )
            }

        case .output:
            if let result = nodes[nodeIndex].resultText {
                VStack(alignment: .leading, spacing: 4) {
                    Text("RESULT")
                        .font(.system(size: 9, weight: .bold, design: .monospaced))
                        .foregroundStyle(.secondary)
                    Text(result)
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.85))
                        .lineLimit(8)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(8)
                        .background(
                            RoundedRectangle(cornerRadius: 8)
                                .fill(.white.opacity(0.03))
                        )
                }
            } else {
                Text("Run the pipeline to see results")
                    .font(.system(size: 11, design: .monospaced))
                    .foregroundStyle(.secondary)
            }
        }
    }

    // MARK: - Bottom Toolbar

    private var bottomToolbar: some View {
        VStack(spacing: 0) {
            Divider().overlay(RheaTheme.cardBorder)
            HStack(spacing: 0) {
                // Node type buttons
                ForEach(NodeType.allCases, id: \.rawValue) { type in
                    Button {
                        addNode(type: type)
                    } label: {
                        VStack(spacing: 2) {
                            Image(systemName: type.icon)
                                .font(.system(size: 14))
                                .foregroundStyle(type.color)
                            Text(type.label)
                                .font(.system(size: 7, weight: .medium, design: .monospaced))
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 6)
                    }
                    .buttonStyle(.plain)
                }

                // Divider
                Rectangle()
                    .fill(RheaTheme.cardBorder)
                    .frame(width: 1, height: 30)

                // Run button
                Button {
                    Task { await runPipeline() }
                } label: {
                    VStack(spacing: 2) {
                        if running {
                            ProgressView()
                                .controlSize(.small)
                                .tint(RheaTheme.green)
                        } else {
                            Image(systemName: "play.fill")
                                .font(.system(size: 14))
                                .foregroundStyle(RheaTheme.green)
                        }
                        Text(running ? "..." : "Run")
                            .font(.system(size: 7, weight: .bold, design: .monospaced))
                            .foregroundStyle(running ? .secondary : RheaTheme.green)
                    }
                    .frame(width: 50)
                    .padding(.vertical, 6)
                }
                .buttonStyle(.plain)
                .disabled(running || nodes.isEmpty)
            }
            .padding(.horizontal, 4)
            .padding(.bottom, 4)
            .background(RheaTheme.card)
        }
    }

    // MARK: - Gestures

    private var canvasDragGesture: some Gesture {
        DragGesture()
            .onChanged { value in
                canvasOffset = CGSize(
                    width: dragCanvasStart.width + value.translation.width,
                    height: dragCanvasStart.height + value.translation.height
                )
            }
            .onEnded { _ in
                dragCanvasStart = canvasOffset
            }
    }

    private var canvasMagnifyGesture: some Gesture {
        MagnifyGesture()
            .onChanged { value in
                let newScale = max(0.3, min(3.0, value.magnification))
                canvasScale = newScale
            }
    }

    private func nodeDragGesture(index: Int) -> some Gesture {
        DragGesture()
            .onChanged { value in
                let scaledTranslation = CGSize(
                    width: value.translation.width / canvasScale,
                    height: value.translation.height / canvasScale
                )
                nodes[index].position = CGPoint(
                    x: nodes[index].position.x + scaledTranslation.width,
                    y: nodes[index].position.y + scaledTranslation.height
                )
            }
    }

    private func outputPortDrag(nodeId: UUID) -> some Gesture {
        DragGesture(coordinateSpace: .global)
            .onChanged { value in
                connectingFrom = nodeId
                connectingEnd = value.location
            }
            .onEnded { value in
                // Find which node the drag ended on
                let dropPoint = canvasToLocal(value.location)
                if let targetNode = findNode(at: dropPoint),
                   targetNode.id != nodeId,
                   targetNode.type.hasInputPort {
                    if let sourceIdx = nodes.firstIndex(where: { $0.id == nodeId }) {
                        if !nodes[sourceIdx].connections.contains(targetNode.id) {
                            withAnimation(.easeOut(duration: 0.2)) {
                                nodes[sourceIdx].connections.append(targetNode.id)
                            }
                        }
                    }
                }
                connectingFrom = nil
            }
    }

    // MARK: - Helpers

    private func canvasToLocal(_ global: CGPoint) -> CGPoint {
        CGPoint(
            x: (global.x - canvasOffset.width) / canvasScale,
            y: (global.y - canvasOffset.height) / canvasScale
        )
    }

    private func findNode(at point: CGPoint) -> PipelineNode? {
        for node in nodes {
            let rect = CGRect(
                x: node.position.x,
                y: node.position.y,
                width: nodeWidth,
                height: nodeHeight
            )
            let expanded = rect.insetBy(dx: -20, dy: -20)
            if expanded.contains(point) {
                return node
            }
        }
        return nil
    }

    private func bezierConnection(from: CGPoint, to: CGPoint) -> Path {
        var path = Path()
        path.move(to: from)
        let dx = abs(to.x - from.x) * 0.5
        let cp1 = CGPoint(x: from.x + dx, y: from.y)
        let cp2 = CGPoint(x: to.x - dx, y: to.y)
        path.addCurve(to: to, control1: cp1, control2: cp2)
        return path
    }

    private func addNode(type: NodeType) {
        // Place new nodes roughly in the center, staggered
        let offset = CGFloat(nodes.count) * 30
        let newNode = PipelineNode(
            type: type,
            position: CGPoint(x: 100 + offset, y: 100 + offset)
        )
        withAnimation(.spring(duration: 0.3)) {
            nodes.append(newNode)
            selectedNodeId = newNode.id
            showConfigPanel = true
        }
    }

    private func binding(for nodeIndex: Int, key: String) -> Binding<String> {
        Binding(
            get: { nodes[nodeIndex].config[key] ?? "" },
            set: { nodes[nodeIndex].config[key] = $0 }
        )
    }

    private func thresholdBinding(nodeIndex: Int) -> Binding<Double> {
        Binding(
            get: { Double(nodes[nodeIndex].config["threshold"] ?? "70") ?? 70 },
            set: { nodes[nodeIndex].config["threshold"] = "\(Int($0))" }
        )
    }

    // MARK: - Pipeline Execution

    private func runPipeline() async {
        guard !nodes.isEmpty else { return }
        running = true
        runError = nil
        defer { running = false }

        // Clear previous results
        for i in nodes.indices {
            nodes[i].resultText = nil
        }

        // Build payload
        let payload = WorkflowPayload(
            nodes: nodes.map { node in
                WorkflowPayload.NodePayload(
                    id: node.id.uuidString,
                    type: node.type.rawValue,
                    connections: node.connections.map { $0.uuidString },
                    config: node.config
                )
            }
        )

        do {
            let response = try await RheaAPI.shared.executeWorkflow(payload)
            
            // Parse response: expect { "results": { "<node_id>": "text", ... } }
            if let results = response["results"] as? [String: Any] {
                withAnimation(.easeOut(duration: 0.3)) {
                    for i in nodes.indices {
                        let key = nodes[i].id.uuidString
                        if let value = results[key] {
                            if let str = value as? String {
                                nodes[i].resultText = str
                            } else if let dict = value as? [String: Any] {
                                // Serialize sub-dict to readable string
                                if let pretty = try? JSONSerialization.data(withJSONObject: dict, options: .prettyPrinted),
                                   let str = String(data: pretty, encoding: .utf8) {
                                    nodes[i].resultText = str
                                }
                            }
                        }
                    }
                }
            }
        } catch {
            runError = error.localizedDescription
            for i in nodes.indices where nodes[i].type == .output {
                nodes[i].resultText = "Error: \(error.localizedDescription)"
            }
        }
    }
}
