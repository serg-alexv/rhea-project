---
sidebar_position: 2
title: NodeEditorView
---

# NodeEditorView

A visual pipeline editor for constructing multi-model verification workflows. Users drag nodes onto an infinite canvas, connect them with wires, configure each node, and execute the pipeline against the Rhea backend.

## Usage

```swift
import RheaKit

struct PipelineTab: View {
    var body: some View {
        NodeEditorView()
    }
}
```

## Node Types

Pipelines are composed of typed nodes, each with a distinct role:

| Type | Icon | Color | Description |
|---|---|---|---|
| `input` | `text.cursor` | Green | Starting claim or prompt |
| `tribunal` | `person.3.fill` | Cyan | Multi-model consensus evaluation |
| `sceptic` | `exclamationmark.shield.fill` | Red | Adversarial challenge node |
| `filter` | `line.3.horizontal.decrease` | Amber | Score threshold gate |
| `proof` | `checkmark.seal.fill` | Purple | Proof-store commit |
| `output` | `doc.text.fill` | White | Final result display |

## Node Configuration

Each node type has configurable parameters:

| Node | Parameters |
|---|---|
| **Input** | `claim` — the text claim to verify |
| **Tribunal** | `models` — number of models (default: 3), `tier` — model tier (`cheap`, `mid`, `premium`) |
| **Sceptic** | `intensity` — challenge strength (`low`, `medium`, `high`) |
| **Filter** | `threshold` — minimum agreement score 0–100 (default: 70) |
| **Proof** | `tag` — proof category label (default: `gem`) |
| **Output** | No configuration needed |

## PipelineNode

The data model backing each node on the canvas:

```swift
public struct PipelineNode: Identifiable, Codable {
    public let id: UUID
    public var type: NodeType
    public var position: CGPoint
    public var connections: [UUID]  // downstream node IDs
    public var config: [String: String]
    public var resultText: String?
}
```

## Canvas Interaction

- **Add nodes** — Tap node-type buttons in the bottom toolbar
- **Move nodes** — Drag to reposition on the infinite canvas
- **Connect nodes** — Drag from an output port to an input port
- **Configure** — Tap a node to open the config panel overlay
- **Pan/zoom** — Pinch to zoom, drag the background to pan
- **Run** — Execute the pipeline via `POST /workflow`

## Execution

When the user taps "Run", `NodeEditorView` serializes all nodes into a `WorkflowPayload` and POSTs it to the backend:

```swift
struct WorkflowPayload: Encodable {
    let nodes: [NodePayload]

    struct NodePayload: Encodable {
        let id: String
        let type: String
        let connections: [String]
        let config: [String: String]
    }
}
```

Results populate each node's `resultText` field and display inline on the canvas.

## Notes

- Nodes have directional ports: input nodes have no input port, output nodes have no output port
- The canvas uses a grid-pattern background for visual alignment
- Connection lines are drawn as paths between port centers
- Pipeline execution requires a running Rhea backend
