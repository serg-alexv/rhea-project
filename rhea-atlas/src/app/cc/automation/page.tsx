'use client'

import { useCallback, useRef, useState, useMemo, useEffect, type DragEvent } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  addEdge,
  useNodesState,
  useEdgesState,
  useReactFlow,
  Handle,
  Position,
  type Connection,
  type Node,
  type Edge,
  type NodeTypes,
  type NodeProps,
  ReactFlowProvider,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import Link from 'next/link'

// ─── Config ──────────────────────────────────────────────────────────
const API = process.env.NEXT_PUBLIC_CC_API ?? 'http://localhost:8400'
const API_KEY = process.env.NEXT_PUBLIC_CC_API_KEY ?? 'dev-bypass'
const headers: Record<string, string> = { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' }

// ─── Node Type Definitions ───────────────────────────────────────────

type NodeTypeConfig = {
  type: string
  label: string
  icon: string
  color: string          // tailwind accent
  borderColor: string    // border class
  bgGlow: string         // glow shadow
  fields: { key: string; label: string; type: 'text' | 'textarea' | 'number' | 'select'; options?: string[] }[]
  inputs: string[]
  outputs: string[]
}

const NODE_TYPE_CONFIGS: NodeTypeConfig[] = [
  {
    type: 'tribunal',
    label: 'Tribunal',
    icon: '\u2696',
    color: 'text-cyan-400',
    borderColor: 'border-cyan-500/30',
    bgGlow: 'shadow-[0_0_12px_rgba(34,211,238,0.08)]',
    fields: [
      { key: 'prompt', label: 'Prompt', type: 'textarea' },
      { key: 'mode', label: 'Mode', type: 'select', options: ['chairman', 'consensus', 'sceptic'] },
      { key: 'k', label: 'Models (k)', type: 'number' },
    ],
    inputs: ['trigger'],
    outputs: ['consensus', 'score'],
  },
  {
    type: 'llm_call',
    label: 'LLM Call',
    icon: '\u2728',
    color: 'text-purple-400',
    borderColor: 'border-purple-500/30',
    bgGlow: 'shadow-[0_0_12px_rgba(168,85,247,0.08)]',
    fields: [
      { key: 'prompt', label: 'Prompt', type: 'textarea' },
      { key: 'model', label: 'Model', type: 'text' },
      { key: 'tier', label: 'Tier', type: 'select', options: ['cheap', 'mid', 'strong', 'frontier'] },
    ],
    inputs: ['trigger'],
    outputs: ['response'],
  },
  {
    type: 'aletheia_search',
    label: 'Aletheia Search',
    icon: '\uD83D\uDD0D',
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/30',
    bgGlow: 'shadow-[0_0_12px_rgba(52,211,153,0.08)]',
    fields: [
      { key: 'query', label: 'Query', type: 'text' },
      { key: 'top_k', label: 'Top K', type: 'number' },
    ],
    inputs: ['trigger'],
    outputs: ['results'],
  },
  {
    type: 'aletheia_store',
    label: 'Aletheia Store',
    icon: '\uD83D\uDCBE',
    color: 'text-emerald-400',
    borderColor: 'border-emerald-500/30',
    bgGlow: 'shadow-[0_0_12px_rgba(52,211,153,0.08)]',
    fields: [
      { key: 'text', label: 'Text', type: 'textarea' },
      { key: 'category', label: 'Category', type: 'select', options: ['fact', 'opinion', 'observation', 'rule'] },
    ],
    inputs: ['trigger', 'data'],
    outputs: ['stored'],
  },
  {
    type: 'http_request',
    label: 'HTTP Request',
    icon: '\uD83C\uDF10',
    color: 'text-amber-400',
    borderColor: 'border-amber-500/30',
    bgGlow: 'shadow-[0_0_12px_rgba(245,158,11,0.08)]',
    fields: [
      { key: 'url', label: 'URL', type: 'text' },
      { key: 'method', label: 'Method', type: 'select', options: ['GET', 'POST', 'PUT', 'DELETE'] },
      { key: 'body', label: 'Body (JSON)', type: 'textarea' },
    ],
    inputs: ['trigger'],
    outputs: ['response', 'status'],
  },
  {
    type: 'transform',
    label: 'Transform',
    icon: '\u2699',
    color: 'text-slate-400',
    borderColor: 'border-slate-500/30',
    bgGlow: 'shadow-[0_0_12px_rgba(148,163,184,0.08)]',
    fields: [
      { key: 'expression', label: 'Expression', type: 'textarea' },
    ],
    inputs: ['input'],
    outputs: ['output'],
  },
  {
    type: 'office_send',
    label: 'Office Send',
    icon: '\uD83D\uDCE8',
    color: 'text-blue-400',
    borderColor: 'border-blue-500/30',
    bgGlow: 'shadow-[0_0_12px_rgba(96,165,250,0.08)]',
    fields: [
      { key: 'receiver', label: 'Receiver', type: 'select', options: ['REX', 'ORION', 'HYPERION', 'B2', 'GEMINI'] },
      { key: 'message', label: 'Message', type: 'textarea' },
    ],
    inputs: ['trigger', 'data'],
    outputs: ['sent'],
  },
  {
    type: 'condition',
    label: 'Condition',
    icon: '\u2747',
    color: 'text-orange-400',
    borderColor: 'border-orange-500/30',
    bgGlow: 'shadow-[0_0_12px_rgba(249,115,22,0.08)]',
    fields: [
      { key: 'expression', label: 'Condition', type: 'text' },
    ],
    inputs: ['input'],
    outputs: ['true', 'false'],
  },
]

const NODE_CONFIG_MAP: Record<string, NodeTypeConfig> = {}
for (const c of NODE_TYPE_CONFIGS) NODE_CONFIG_MAP[c.type] = c

// ─── Custom Node Component ──────────────────────────────────────────

function AutomationNode({ data, selected }: NodeProps) {
  const config = NODE_CONFIG_MAP[data.nodeType as string]
  if (!config) return <div className="p-2 text-red-400">Unknown node</div>

  return (
    <div
      className={`
        min-w-[180px] max-w-[240px] rounded-lg bg-white/[0.03] backdrop-blur-sm
        border ${config.borderColor} ${config.bgGlow}
        ${selected ? 'ring-1 ring-white/20' : ''}
        transition-shadow duration-150
      `}
    >
      {/* Header */}
      <div className={`flex items-center gap-2 px-3 py-2 border-b border-white/[0.06] rounded-t-lg`}>
        <span className="text-base">{config.icon}</span>
        <span className={`text-xs font-bold uppercase tracking-wider ${config.color}`}>{config.label}</span>
      </div>

      {/* Compact config display */}
      <div className="px-3 py-2 space-y-1">
        {config.fields.slice(0, 2).map(f => {
          const val = (data.config as Record<string, string>)?.[f.key]
          return val ? (
            <div key={f.key} className="text-[10px] text-white/40 truncate">
              <span className="text-white/20">{f.label}:</span>{' '}
              <span className="text-white/60">{String(val).slice(0, 40)}</span>
            </div>
          ) : null
        })}
        {!Object.values((data.config as Record<string, string>) || {}).some(Boolean) && (
          <div className="text-[10px] text-white/20 italic">Click to configure</div>
        )}
      </div>

      {/* Input handles */}
      {config.inputs.map((inp, i) => (
        <Handle
          key={`in-${inp}`}
          type="target"
          position={Position.Left}
          id={inp}
          style={{
            top: `${30 + i * 24}px`,
            background: '#1e293b',
            border: '2px solid rgba(34, 211, 238, 0.4)',
            width: 10,
            height: 10,
          }}
          title={inp}
        />
      ))}

      {/* Output handles */}
      {config.outputs.map((out, i) => (
        <Handle
          key={`out-${out}`}
          type="source"
          position={Position.Right}
          id={out}
          style={{
            top: `${30 + i * 24}px`,
            background: '#1e293b',
            border: '2px solid rgba(52, 211, 153, 0.4)',
            width: 10,
            height: 10,
          }}
          title={out}
        />
      ))}
    </div>
  )
}

// ─── Sidebar ─────────────────────────────────────────────────────────

function Sidebar() {
  const onDragStart = (event: DragEvent<HTMLDivElement>, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div className="w-52 shrink-0 border-r border-white/[0.06] p-3 overflow-y-auto">
      <h2 className="text-xs font-bold uppercase tracking-widest text-cyan-400/80 mb-3">Node Types</h2>
      <div className="space-y-1.5">
        {NODE_TYPE_CONFIGS.map(c => (
          <div
            key={c.type}
            draggable
            onDragStart={e => onDragStart(e, c.type)}
            className={`
              flex items-center gap-2 px-2.5 py-2 rounded-lg
              bg-white/[0.03] border ${c.borderColor}
              hover:bg-white/[0.06] cursor-grab active:cursor-grabbing
              transition-colors select-none
            `}
          >
            <span className="text-sm">{c.icon}</span>
            <span className={`text-xs font-medium ${c.color}`}>{c.label}</span>
          </div>
        ))}
      </div>
      <div className="mt-6 text-[10px] text-white/20 leading-relaxed">
        Drag nodes onto the canvas. Connect output handles (right) to input handles (left) to build a workflow.
      </div>
    </div>
  )
}

// ─── Inspector Panel ─────────────────────────────────────────────────

function Inspector({
  node,
  onConfigChange,
  onClose,
}: {
  node: Node | null
  onConfigChange: (nodeId: string, config: Record<string, string>) => void
  onClose: () => void
}) {
  if (!node) return null

  const config = NODE_CONFIG_MAP[node.data.nodeType as string]
  if (!config) return null

  const nodeConfig = (node.data.config as Record<string, string>) || {}

  const updateField = (key: string, value: string) => {
    onConfigChange(node.id, { ...nodeConfig, [key]: value })
  }

  return (
    <div className="w-72 shrink-0 border-l border-white/[0.06] p-3 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-base">{config.icon}</span>
          <h2 className={`text-xs font-bold uppercase tracking-widest ${config.color}`}>{config.label}</h2>
        </div>
        <button onClick={onClose} className="text-white/30 hover:text-white/60 text-sm transition-colors">\u2715</button>
      </div>

      <div className="space-y-3">
        {/* Node ID */}
        <div>
          <label className="block text-[10px] text-white/30 uppercase tracking-wider mb-1">Node ID</label>
          <div className="text-xs font-mono text-white/50 bg-white/[0.03] rounded px-2 py-1.5">{node.id}</div>
        </div>

        {/* Config fields */}
        {config.fields.map(f => (
          <div key={f.key}>
            <label className="block text-[10px] text-white/30 uppercase tracking-wider mb-1">{f.label}</label>
            {f.type === 'textarea' ? (
              <textarea
                value={nodeConfig[f.key] || ''}
                onChange={e => updateField(f.key, e.target.value)}
                rows={3}
                className="w-full bg-white/[0.05] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white/90 placeholder-white/20 focus:outline-none focus:border-cyan-500/50 resize-none"
                placeholder={`Enter ${f.label.toLowerCase()}...`}
              />
            ) : f.type === 'select' ? (
              <select
                value={nodeConfig[f.key] || ''}
                onChange={e => updateField(f.key, e.target.value)}
                className="w-full bg-white/[0.05] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white/90 focus:outline-none focus:border-cyan-500/50"
              >
                <option value="" className="bg-[#0a0a0f]">Select...</option>
                {f.options?.map(o => (
                  <option key={o} value={o} className="bg-[#0a0a0f]">{o}</option>
                ))}
              </select>
            ) : f.type === 'number' ? (
              <input
                type="number"
                value={nodeConfig[f.key] || ''}
                onChange={e => updateField(f.key, e.target.value)}
                className="w-full bg-white/[0.05] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white/90 placeholder-white/20 focus:outline-none focus:border-cyan-500/50"
                placeholder="0"
              />
            ) : (
              <input
                type="text"
                value={nodeConfig[f.key] || ''}
                onChange={e => updateField(f.key, e.target.value)}
                className="w-full bg-white/[0.05] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-white/90 placeholder-white/20 focus:outline-none focus:border-cyan-500/50"
                placeholder={`Enter ${f.label.toLowerCase()}...`}
              />
            )}
          </div>
        ))}

        {/* Handle info */}
        <div className="pt-2 border-t border-white/[0.06]">
          <label className="block text-[10px] text-white/30 uppercase tracking-wider mb-1">Inputs</label>
          <div className="flex gap-1 flex-wrap">
            {config.inputs.map(h => (
              <span key={h} className="text-[10px] bg-cyan-500/10 text-cyan-400/70 px-1.5 py-0.5 rounded">{h}</span>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-[10px] text-white/30 uppercase tracking-wider mb-1">Outputs</label>
          <div className="flex gap-1 flex-wrap">
            {config.outputs.map(h => (
              <span key={h} className="text-[10px] bg-emerald-500/10 text-emerald-400/70 px-1.5 py-0.5 rounded">{h}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Main Flow Editor ────────────────────────────────────────────────

function FlowEditor() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition } = useReactFlow()

  const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[])
  const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [workflowName, setWorkflowName] = useState('Untitled Workflow')
  const [workflowId, setWorkflowId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const nodeIdCounter = useRef(0)

  const nodeTypes: NodeTypes = useMemo(() => ({
    tribunal: AutomationNode,
    llm_call: AutomationNode,
    aletheia_search: AutomationNode,
    aletheia_store: AutomationNode,
    http_request: AutomationNode,
    transform: AutomationNode,
    office_send: AutomationNode,
    condition: AutomationNode,
  }), [])

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges(eds =>
        addEdge(
          {
            ...params,
            type: 'smoothstep',
            animated: true,
            style: { stroke: 'rgba(34, 211, 238, 0.3)', strokeWidth: 2 },
          },
          eds,
        ),
      )
    },
    [setEdges],
  )

  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault()

      const nodeType = event.dataTransfer.getData('application/reactflow')
      if (!nodeType || !NODE_CONFIG_MAP[nodeType]) return

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      nodeIdCounter.current += 1
      const newNode: Node = {
        id: `${nodeType}_${nodeIdCounter.current}`,
        type: nodeType,
        position,
        data: {
          nodeType,
          config: {},
        },
      }

      setNodes(nds => [...nds, newNode])
    },
    [screenToFlowPosition, setNodes],
  )

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  // Keep selectedNode in sync with node state
  useEffect(() => {
    if (selectedNode) {
      const updated = nodes.find(n => n.id === selectedNode.id)
      if (updated) setSelectedNode(updated)
    }
  }, [nodes, selectedNode])

  const onConfigChange = useCallback(
    (nodeId: string, config: Record<string, string>) => {
      setNodes(nds =>
        nds.map(n =>
          n.id === nodeId ? { ...n, data: { ...n.data, config } } : n,
        ),
      )
    },
    [setNodes],
  )

  const showStatus = (msg: string) => {
    setStatusMsg(msg)
    setTimeout(() => setStatusMsg(null), 3000)
  }

  const saveWorkflow = async () => {
    setSaving(true)
    try {
      const payload = {
        name: workflowName,
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type,
          position: n.position,
          data: n.data,
        })),
        edges: edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
        })),
      }
      const res = await fetch(`${API}/workflows`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (data.id) setWorkflowId(data.id)
      showStatus('Saved')
    } catch {
      showStatus('Save failed - API unreachable')
    } finally {
      setSaving(false)
    }
  }

  const executeWorkflow = async () => {
    if (!workflowId) {
      showStatus('Save first before executing')
      return
    }
    setExecuting(true)
    try {
      const res = await fetch(`${API}/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers,
      })
      const data = await res.json()
      showStatus(data.status === 'running' ? 'Executing...' : `Status: ${data.status || 'sent'}`)
    } catch {
      showStatus('Execute failed - API unreachable')
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[200] bg-[#0a0a0f] text-white overflow-hidden flex flex-col">
      {/* Top toolbar */}
      <div className="border-b border-white/[0.06] px-4 py-2 flex items-center gap-3 shrink-0">
        <Link
          href="/cc"
          className="text-white/40 hover:text-white/70 text-xs font-medium transition-colors flex items-center gap-1"
        >
          <span>\u2190</span> CC
        </Link>
        <div className="w-px h-4 bg-white/10" />
        <h1 className="text-sm font-bold tracking-wider text-white/80">AUTOMATION</h1>
        <div className="w-px h-4 bg-white/10" />
        <input
          value={workflowName}
          onChange={e => setWorkflowName(e.target.value)}
          className="bg-white/[0.05] border border-white/10 rounded-lg px-3 py-1 text-xs text-white/80 placeholder-white/20 focus:outline-none focus:border-cyan-500/50 w-56"
          placeholder="Workflow name..."
        />
        <div className="flex items-center gap-2 ml-auto">
          {statusMsg && (
            <span className="text-[10px] text-cyan-400/70 font-mono animate-pulse">{statusMsg}</span>
          )}
          <button
            onClick={saveWorkflow}
            disabled={saving}
            className="px-3 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/40 text-cyan-300 rounded-lg text-xs font-medium transition-colors disabled:opacity-30"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button
            onClick={executeWorkflow}
            disabled={executing || !workflowId}
            className="px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-300 rounded-lg text-xs font-medium transition-colors disabled:opacity-30"
          >
            {executing ? 'Running...' : 'Execute'}
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div className="border-b border-white/[0.06] px-4 flex items-center gap-0 shrink-0">
        <Link
          href="/cc"
          className="px-4 py-2 text-xs font-medium text-white/40 hover:text-white/60 transition-colors border-b-2 border-transparent"
        >
          Monitor
        </Link>
        <div className="px-4 py-2 text-xs font-medium text-cyan-400 border-b-2 border-cyan-400">
          Automation
        </div>
      </div>

      {/* Main area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop check — hide on mobile */}
        <div className="contents max-sm:hidden">
          <Sidebar />

          <div ref={reactFlowWrapper} className="flex-1 relative">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              nodeTypes={nodeTypes}
              defaultEdgeOptions={{
                type: 'smoothstep',
                animated: true,
                style: { stroke: 'rgba(34, 211, 238, 0.3)', strokeWidth: 2 },
              }}
              fitView
              proOptions={{ hideAttribution: true }}
              className="bg-[#0a0a0f]"
            >
              <Background color="rgba(255,255,255,0.03)" gap={20} size={1} />
              <Controls
                showInteractive={false}
                className="!bg-white/[0.05] !border-white/10 !rounded-lg [&>button]:!bg-transparent [&>button]:!border-white/10 [&>button]:!text-white/50 [&>button:hover]:!bg-white/10"
              />
              <MiniMap
                nodeColor={() => 'rgba(34, 211, 238, 0.3)'}
                maskColor="rgba(0, 0, 0, 0.7)"
                className="!bg-white/[0.03] !border-white/10 !rounded-lg"
              />
              {nodes.length === 0 && (
                <Panel position="top-center">
                  <div className="mt-32 text-center text-white/20">
                    <div className="text-3xl mb-3 opacity-30">\u26A1</div>
                    <div className="text-sm">Drag nodes from the sidebar to build a workflow</div>
                    <div className="text-xs mt-1 text-white/10">Connect outputs to inputs to define execution flow</div>
                  </div>
                </Panel>
              )}
            </ReactFlow>
          </div>

          <Inspector
            node={selectedNode}
            onConfigChange={onConfigChange}
            onClose={() => setSelectedNode(null)}
          />
        </div>

        {/* Mobile fallback */}
        <div className="hidden max-sm:flex flex-1 items-center justify-center">
          <div className="text-center text-white/30 px-8">
            <div className="text-3xl mb-3">\uD83D\uDDA5</div>
            <div className="text-sm font-medium">Automation requires desktop</div>
            <div className="text-xs mt-1 text-white/20">The node editor needs a wider viewport to work properly.</div>
            <Link
              href="/cc"
              className="inline-block mt-4 px-4 py-2 bg-cyan-600/20 hover:bg-cyan-600/40 text-cyan-300 rounded-lg text-xs font-medium transition-colors"
            >
              Back to Monitor
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Page Export (with ReactFlowProvider) ─────────────────────────────

export default function AutomationPage() {
  return (
    <ReactFlowProvider>
      <FlowEditor />
    </ReactFlowProvider>
  )
}
