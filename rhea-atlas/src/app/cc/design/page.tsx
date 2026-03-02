'use client'

import { useRef, useState, useCallback, useEffect } from 'react'
import Link from 'next/link'

// ─── Types ───────────────────────────────────────────────────────────

type SwiftComponent =
  | 'Text' | 'Button' | 'Image' | 'Toggle' | 'Slider' | 'TextField'
  | 'VStack' | 'HStack' | 'ZStack' | 'Spacer' | 'Divider'
  | 'Rectangle' | 'Circle' | 'RoundedRectangle' | 'Capsule'

interface DesignNode {
  id: string
  type: SwiftComponent
  x: number; y: number
  w: number; h: number
  props: Record<string, string | number | boolean>
  children: string[]   // child node IDs for stacks
  parentId?: string
}

interface HistoryEntry {
  nodes: DesignNode[]
  selectedIds: Set<string>
}

interface SavedDesign {
  name: string
  timestamp: number
  nodes: DesignNode[]
}

const STORAGE_KEY = 'rhea-design-saved'
const AUTOSAVE_KEY = 'rhea-design-autosave'
const GRID_SIZE = 8

// ─── Helpers ─────────────────────────────────────────────────────────

const uid = () => Math.random().toString(36).slice(2, 10)

function snapToGrid(v: number): number {
  return Math.round(v / GRID_SIZE) * GRID_SIZE
}

function cloneNode(node: DesignNode, offsetX = 20, offsetY = 20): DesignNode {
  return { ...node, id: uid(), x: node.x + offsetX, y: node.y + offsetY, props: { ...node.props }, children: [...node.children] }
}

function loadSavedDesigns(): SavedDesign[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

function saveSavedDesigns(designs: SavedDesign[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(designs)) } catch {}
}

const COMPONENT_PALETTE: { label: string; items: { type: SwiftComponent; icon: string; w: number; h: number }[] }[] = [
  {
    label: 'Views',
    items: [
      { type: 'Text', icon: 'T', w: 120, h: 32 },
      { type: 'Button', icon: '▢', w: 140, h: 44 },
      { type: 'Image', icon: '🖼', w: 100, h: 100 },
      { type: 'TextField', icon: '⌨', w: 200, h: 40 },
      { type: 'Toggle', icon: '◑', w: 60, h: 32 },
      { type: 'Slider', icon: '─●─', w: 200, h: 32 },
    ],
  },
  {
    label: 'Layout',
    items: [
      { type: 'VStack', icon: '⫿', w: 200, h: 200 },
      { type: 'HStack', icon: '⫞', w: 300, h: 80 },
      { type: 'ZStack', icon: '▣', w: 200, h: 200 },
      { type: 'Spacer', icon: '↕', w: 20, h: 40 },
      { type: 'Divider', icon: '─', w: 200, h: 2 },
    ],
  },
  {
    label: 'Shapes',
    items: [
      { type: 'Rectangle', icon: '□', w: 120, h: 80 },
      { type: 'Circle', icon: '○', w: 80, h: 80 },
      { type: 'RoundedRectangle', icon: '▢', w: 120, h: 80 },
      { type: 'Capsule', icon: '⬭', w: 140, h: 50 },
    ],
  },
]

const DEFAULT_PROPS: Record<SwiftComponent, Record<string, string | number | boolean>> = {
  Text:             { text: 'Hello, World!', font: '.body', foreground: '#000000', bold: false },
  Button:           { label: 'Tap Me', style: 'borderedProminent', foreground: '#ffffff', background: '#007AFF' },
  Image:            { systemName: 'star.fill', foreground: '#007AFF', resizable: true },
  TextField:        { placeholder: 'Enter text...', style: 'roundedBorder', foreground: '#000000' },
  Toggle:           { label: 'Toggle', isOn: true, tint: '#34C759' },
  Slider:           { value: 0.5, min: 0, max: 1, tint: '#007AFF' },
  VStack:           { alignment: 'center', spacing: 8, background: 'transparent', cornerRadius: 0 },
  HStack:           { alignment: 'center', spacing: 8, background: 'transparent', cornerRadius: 0 },
  ZStack:           { alignment: 'center', background: 'transparent', cornerRadius: 0 },
  Spacer:           {},
  Divider:          {},
  Rectangle:        { fill: '#007AFF', cornerRadius: 0, strokeColor: 'transparent', strokeWidth: 0 },
  Circle:           { fill: '#34C759', strokeColor: 'transparent', strokeWidth: 0 },
  RoundedRectangle: { fill: '#FF9500', cornerRadius: 12, strokeColor: 'transparent', strokeWidth: 0 },
  Capsule:          { fill: '#AF52DE', strokeColor: 'transparent', strokeWidth: 0 },
}

const FONT_OPTIONS = ['.largeTitle', '.title', '.title2', '.title3', '.headline', '.body', '.callout', '.subheadline', '.footnote', '.caption', '.caption2']
const STYLE_OPTIONS = ['borderedProminent', 'bordered', 'borderless', 'plain']

// ─── SwiftUI Code Generator ─────────────────────────────────────────

function generateSwiftUI(nodes: DesignNode[], rootIds: string[]): string {
  const nodeMap = new Map(nodes.map(n => [n.id, n]))

  function indent(code: string, level: number): string {
    const pad = '    '.repeat(level)
    return code.split('\n').map(l => l.trim() ? pad + l : '').join('\n')
  }

  function gen(id: string, level: number): string {
    const node = nodeMap.get(id)
    if (!node) return ''
    const p = node.props
    const pad = '    '.repeat(level)

    switch (node.type) {
      case 'Text':
        return `${pad}Text("${p.text || ''}")${p.font ? `\n${pad}    .font(${p.font})` : ''}${p.bold ? `\n${pad}    .bold()` : ''}${p.foreground && p.foreground !== '#000000' ? `\n${pad}    .foregroundStyle(Color(hex: "${p.foreground}"))` : ''}`

      case 'Button':
        return `${pad}Button("${p.label || ''}") {\n${pad}    // action\n${pad}}${p.style ? `\n${pad}.buttonStyle(.${p.style})` : ''}`

      case 'Image':
        return `${pad}Image(systemName: "${p.systemName || 'star'}")${p.resizable ? `\n${pad}    .resizable()\n${pad}    .scaledToFit()` : ''}${p.foreground ? `\n${pad}    .foregroundStyle(Color(hex: "${p.foreground}"))` : ''}\n${pad}    .frame(width: ${node.w}, height: ${node.h})`

      case 'TextField':
        return `${pad}TextField("${p.placeholder || ''}", text: $text)${p.style === 'roundedBorder' ? `\n${pad}    .textFieldStyle(.roundedBorder)` : ''}`

      case 'Toggle':
        return `${pad}Toggle("${p.label || ''}", isOn: $isOn)${p.tint ? `\n${pad}    .tint(Color(hex: "${p.tint}"))` : ''}`

      case 'Slider':
        return `${pad}Slider(value: $sliderValue, in: ${p.min ?? 0}...${p.max ?? 1})${p.tint ? `\n${pad}    .tint(Color(hex: "${p.tint}"))` : ''}`

      case 'VStack':
      case 'HStack':
      case 'ZStack': {
        const childCode = node.children.map(cid => gen(cid, level + 1)).filter(Boolean).join('\n')
        const bg = p.background && p.background !== 'transparent' ? `\n${pad}.background(Color(hex: "${p.background}"))` : ''
        const cr = p.cornerRadius && Number(p.cornerRadius) > 0 ? `\n${pad}.clipShape(RoundedRectangle(cornerRadius: ${p.cornerRadius}))` : ''
        return `${pad}${node.type}(alignment: .${p.alignment || 'center'}${p.spacing !== undefined ? `, spacing: ${p.spacing}` : ''}) {\n${childCode || `${pad}    // children`}\n${pad}}${bg}${cr}`
      }

      case 'Spacer':
        return `${pad}Spacer()`

      case 'Divider':
        return `${pad}Divider()`

      case 'Rectangle':
        return `${pad}Rectangle()\n${pad}    .fill(Color(hex: "${p.fill || '#007AFF'}"))${Number(p.cornerRadius) > 0 ? `\n${pad}    .clipShape(RoundedRectangle(cornerRadius: ${p.cornerRadius}))` : ''}\n${pad}    .frame(width: ${node.w}, height: ${node.h})`

      case 'Circle':
        return `${pad}Circle()\n${pad}    .fill(Color(hex: "${p.fill || '#34C759'}"))\n${pad}    .frame(width: ${Math.min(node.w, node.h)}, height: ${Math.min(node.w, node.h)})`

      case 'RoundedRectangle':
        return `${pad}RoundedRectangle(cornerRadius: ${p.cornerRadius || 12})\n${pad}    .fill(Color(hex: "${p.fill || '#FF9500'}"))\n${pad}    .frame(width: ${node.w}, height: ${node.h})`

      case 'Capsule':
        return `${pad}Capsule()\n${pad}    .fill(Color(hex: "${p.fill || '#AF52DE'}"))\n${pad}    .frame(width: ${node.w}, height: ${node.h})`

      default:
        return `${pad}// TODO: ${node.type}`
    }
  }

  const body = rootIds.map(id => gen(id, 2)).filter(Boolean).join('\n')

  return `import SwiftUI

struct DesignView: View {
    @State private var text = ""
    @State private var isOn = true
    @State private var sliderValue: Double = 0.5

    var body: some View {
${body || '        Text("Empty canvas")'}
    }
}

// Color hex extension (add to project once)
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))
        let scanner = Scanner(string: hex)
        var rgbValue: UInt64 = 0
        scanner.scanHexInt64(&rgbValue)
        self.init(
            red: Double((rgbValue >> 16) & 0xFF) / 255.0,
            green: Double((rgbValue >> 8) & 0xFF) / 255.0,
            blue: Double(rgbValue & 0xFF) / 255.0
        )
    }
}

#Preview {
    DesignView()
}`
}

// ─── Node Renderer (Canvas) ─────────────────────────────────────────

function NodeRenderer({ node, selected, onSelect, onDragStart, zIndex }: {
  node: DesignNode
  selected: boolean
  onSelect: (e: React.MouseEvent) => void
  onDragStart: (e: React.MouseEvent) => void
  zIndex: number
}) {
  const p = node.props
  const isStack = ['VStack', 'HStack', 'ZStack'].includes(node.type)
  const isShape = ['Rectangle', 'Circle', 'RoundedRectangle', 'Capsule'].includes(node.type)

  const baseStyle: React.CSSProperties = {
    position: 'absolute',
    left: node.x,
    top: node.y,
    width: node.w,
    height: node.h,
    cursor: 'move',
    outline: selected ? '2px solid #007AFF' : '1px solid rgba(128,128,128,0.3)',
    outlineOffset: 2,
    borderRadius: node.type === 'Circle' ? '50%' : node.type === 'Capsule' ? 999 : Number(p.cornerRadius) || 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    userSelect: 'none',
    zIndex,
  }

  let content: React.ReactNode = null
  let bgColor = 'transparent'

  switch (node.type) {
    case 'Text':
      content = <span style={{ color: String(p.foreground || '#000'), fontSize: 14, fontWeight: p.bold ? 700 : 400 }}>{String(p.text || 'Text')}</span>
      break
    case 'Button':
      bgColor = String(p.background || '#007AFF')
      content = <span style={{ color: String(p.foreground || '#fff'), fontSize: 14, fontWeight: 600, padding: '6px 16px' }}>{String(p.label || 'Button')}</span>
      baseStyle.borderRadius = 8
      break
    case 'Image':
      content = <span style={{ fontSize: 28, color: String(p.foreground || '#007AFF') }}>★</span>
      break
    case 'TextField':
      bgColor = '#f1f5f9'
      content = <span style={{ color: '#94a3b8', fontSize: 13, padding: '0 8px' }}>{String(p.placeholder || 'Enter text...')}</span>
      baseStyle.borderRadius = 6
      baseStyle.border = '1px solid #cbd5e1'
      break
    case 'Toggle':
      content = (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '0 8px' }}>
          <span style={{ fontSize: 13 }}>{String(p.label || 'Toggle')}</span>
          <div style={{ width: 44, height: 26, borderRadius: 13, background: p.isOn ? String(p.tint || '#34C759') : '#e2e8f0', position: 'relative' }}>
            <div style={{ width: 22, height: 22, borderRadius: 11, background: '#fff', position: 'absolute', top: 2, left: p.isOn ? 20 : 2, transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.2)' }} />
          </div>
        </div>
      )
      break
    case 'Slider':
      content = (
        <div style={{ width: '100%', padding: '0 8px' }}>
          <div style={{ height: 4, borderRadius: 2, background: '#e2e8f0', position: 'relative' }}>
            <div style={{ position: 'absolute', left: 0, top: 0, height: 4, borderRadius: 2, width: `${(Number(p.value) || 0.5) * 100}%`, background: String(p.tint || '#007AFF') }} />
            <div style={{ position: 'absolute', top: -8, left: `${(Number(p.value) || 0.5) * 100}%`, transform: 'translateX(-50%)', width: 20, height: 20, borderRadius: 10, background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.3)' }} />
          </div>
        </div>
      )
      break
    case 'VStack':
    case 'HStack':
    case 'ZStack':
      bgColor = String(p.background) !== 'transparent' ? String(p.background) : 'rgba(100,149,237,0.05)'
      baseStyle.border = '1px dashed rgba(100,149,237,0.4)'
      baseStyle.flexDirection = node.type === 'HStack' ? 'row' : 'column'
      baseStyle.gap = Number(p.spacing) || 8
      content = <span style={{ fontSize: 11, color: '#94a3b8', position: 'absolute', top: 2, left: 6 }}>{node.type}</span>
      break
    case 'Spacer':
      baseStyle.border = '1px dashed #e2e8f0'
      content = <span style={{ fontSize: 10, color: '#cbd5e1' }}>Spacer</span>
      break
    case 'Divider':
      bgColor = '#e2e8f0'
      break
    case 'Rectangle':
    case 'RoundedRectangle':
    case 'Capsule':
      bgColor = String(p.fill || '#007AFF')
      break
    case 'Circle':
      bgColor = String(p.fill || '#34C759')
      break
  }

  return (
    <div
      style={{ ...baseStyle, backgroundColor: bgColor }}
      onMouseDown={(e) => { e.stopPropagation(); onSelect(e); onDragStart(e) }}
    >
      {content}
    </div>
  )
}

// ─── Property Inspector ─────────────────────────────────────────────

function Inspector({ node, onChange, onDelete }: {
  node: DesignNode
  onChange: (id: string, props: Record<string, string | number | boolean>) => void
  onDelete: (id: string) => void
}) {
  const p = node.props

  function set(key: string, value: string | number | boolean) {
    onChange(node.id, { ...p, [key]: value })
  }

  const inputStyle: React.CSSProperties = { width: '100%', background: '#1e293b', border: '1px solid #334155', borderRadius: 4, padding: '4px 6px', color: '#e2e8f0', fontSize: 12 }
  const labelStyle: React.CSSProperties = { fontSize: 11, color: '#94a3b8', marginBottom: 2 }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', borderBottom: '1px solid #334155', paddingBottom: 4 }}>{node.type}</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
        <div><div style={labelStyle}>x</div><input type="number" value={node.x} onChange={e => onChange(node.id, { ...p, __x: Number(e.target.value) })} style={inputStyle} /></div>
        <div><div style={labelStyle}>y</div><input type="number" value={node.y} onChange={e => onChange(node.id, { ...p, __y: Number(e.target.value) })} style={inputStyle} /></div>
        <div><div style={labelStyle}>w</div><input type="number" value={node.w} onChange={e => onChange(node.id, { ...p, __w: Number(e.target.value) })} style={inputStyle} /></div>
        <div><div style={labelStyle}>h</div><input type="number" value={node.h} onChange={e => onChange(node.id, { ...p, __h: Number(e.target.value) })} style={inputStyle} /></div>
      </div>

      {p.text !== undefined && (
        <div><div style={labelStyle}>Text</div><input value={String(p.text)} onChange={e => set('text', e.target.value)} style={inputStyle} /></div>
      )}
      {p.label !== undefined && (
        <div><div style={labelStyle}>Label</div><input value={String(p.label)} onChange={e => set('label', e.target.value)} style={inputStyle} /></div>
      )}
      {p.placeholder !== undefined && (
        <div><div style={labelStyle}>Placeholder</div><input value={String(p.placeholder)} onChange={e => set('placeholder', e.target.value)} style={inputStyle} /></div>
      )}
      {p.systemName !== undefined && (
        <div><div style={labelStyle}>SF Symbol</div><input value={String(p.systemName)} onChange={e => set('systemName', e.target.value)} style={inputStyle} /></div>
      )}
      {p.font !== undefined && (
        <div><div style={labelStyle}>Font</div>
          <select value={String(p.font)} onChange={e => set('font', e.target.value)} style={inputStyle}>
            {FONT_OPTIONS.map(f => <option key={f} value={f}>{f.replace('.', '')}</option>)}
          </select>
        </div>
      )}
      {p.style !== undefined && node.type === 'Button' && (
        <div><div style={labelStyle}>Style</div>
          <select value={String(p.style)} onChange={e => set('style', e.target.value)} style={inputStyle}>
            {STYLE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      )}
      {p.bold !== undefined && (
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#e2e8f0', cursor: 'pointer' }}>
          <input type="checkbox" checked={!!p.bold} onChange={e => set('bold', e.target.checked)} /> Bold
        </label>
      )}
      {p.foreground !== undefined && (
        <div><div style={labelStyle}>Color</div><input type="color" value={String(p.foreground)} onChange={e => set('foreground', e.target.value)} style={{ ...inputStyle, height: 28, padding: 2 }} /></div>
      )}
      {p.background !== undefined && (
        <div><div style={labelStyle}>Background</div><input type="color" value={String(p.background === 'transparent' ? '#ffffff' : p.background)} onChange={e => set('background', e.target.value)} style={{ ...inputStyle, height: 28, padding: 2 }} /></div>
      )}
      {p.fill !== undefined && (
        <div><div style={labelStyle}>Fill</div><input type="color" value={String(p.fill)} onChange={e => set('fill', e.target.value)} style={{ ...inputStyle, height: 28, padding: 2 }} /></div>
      )}
      {p.tint !== undefined && (
        <div><div style={labelStyle}>Tint</div><input type="color" value={String(p.tint)} onChange={e => set('tint', e.target.value)} style={{ ...inputStyle, height: 28, padding: 2 }} /></div>
      )}
      {p.cornerRadius !== undefined && (
        <div><div style={labelStyle}>Corner Radius</div><input type="number" min={0} value={Number(p.cornerRadius)} onChange={e => set('cornerRadius', Number(e.target.value))} style={inputStyle} /></div>
      )}
      {p.spacing !== undefined && (
        <div><div style={labelStyle}>Spacing</div><input type="number" min={0} value={Number(p.spacing)} onChange={e => set('spacing', Number(e.target.value))} style={inputStyle} /></div>
      )}
      {p.alignment !== undefined && (
        <div><div style={labelStyle}>Alignment</div>
          <select value={String(p.alignment)} onChange={e => set('alignment', e.target.value)} style={inputStyle}>
            {['leading', 'center', 'trailing', 'top', 'bottom'].map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      )}

      <button onClick={() => onDelete(node.id)} style={{ marginTop: 8, padding: '6px 12px', background: '#dc2626', border: 'none', borderRadius: 6, color: '#fff', fontSize: 12, cursor: 'pointer' }}>Delete</button>
    </div>
  )
}

// ─── Toolbar Button ─────────────────────────────────────────────────

function ToolBtn({ label, icon, onClick, active, disabled, tooltip }: {
  label?: string; icon: string; onClick: () => void; active?: boolean; disabled?: boolean; tooltip?: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={tooltip || label}
      style={{
        padding: '4px 8px', background: active ? '#007AFF' : '#1e293b',
        border: '1px solid #334155', borderRadius: 4, color: disabled ? '#475569' : '#e2e8f0',
        fontSize: 12, cursor: disabled ? 'default' : 'pointer', display: 'flex', alignItems: 'center', gap: 4,
        opacity: disabled ? 0.5 : 1,
      }}
    >
      <span style={{ fontSize: 13 }}>{icon}</span>
      {label && <span>{label}</span>}
    </button>
  )
}

// ─── Save/Load Modal ────────────────────────────────────────────────

function SaveLoadModal({ onClose, onLoad }: {
  onClose: () => void
  onLoad: (nodes: DesignNode[]) => void
}) {
  const [designs, setDesigns] = useState<SavedDesign[]>([])

  useEffect(() => { setDesigns(loadSavedDesigns()) }, [])

  function handleDelete(idx: number) {
    const next = designs.filter((_, i) => i !== idx)
    saveSavedDesigns(next)
    setDesigns(next)
  }

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.6)' }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ width: 380, maxHeight: '60vh', background: '#1e293b', borderRadius: 12, border: '1px solid #334155', padding: 16, overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: '#f8fafc', margin: 0 }}>Saved Designs</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: 16, cursor: 'pointer' }}>x</button>
        </div>
        {designs.length === 0 ? (
          <div style={{ fontSize: 12, color: '#64748b', padding: 16, textAlign: 'center' }}>No saved designs yet. Use the save button to store your current design.</div>
        ) : (
          designs.map((d, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', borderBottom: '1px solid #334155' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, color: '#e2e8f0' }}>{d.name}</div>
                <div style={{ fontSize: 10, color: '#64748b' }}>{new Date(d.timestamp).toLocaleString()} — {d.nodes.length} components</div>
              </div>
              <button onClick={() => { onLoad(d.nodes); onClose() }} style={{ padding: '3px 10px', background: '#007AFF', border: 'none', borderRadius: 4, color: '#fff', fontSize: 11, cursor: 'pointer' }}>Load</button>
              <button onClick={() => handleDelete(i)} style={{ padding: '3px 8px', background: '#dc2626', border: 'none', borderRadius: 4, color: '#fff', fontSize: 11, cursor: 'pointer' }}>x</button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// ─── Main Page ───────────────────────────────────────────────────────

export default function DesignPage() {
  const [nodes, setNodes] = useState<DesignNode[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [showCode, setShowCode] = useState(false)
  const [dragState, setDragState] = useState<{ ids: string[]; offsets: Map<string, { ox: number; oy: number }> } | null>(null)
  const [deviceFrame, setDeviceFrame] = useState<'iphone15' | 'iphone_se' | 'ipad'>('iphone15')
  const [snapEnabled, setSnapEnabled] = useState(false)
  const [showSaveLoad, setShowSaveLoad] = useState(false)

  // Undo/redo stacks
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const isUndoRedoRef = useRef(false)

  const canvasRef = useRef<HTMLDivElement>(null)

  const DEVICE_SIZES = {
    iphone15: { w: 393, h: 852, label: 'iPhone 15' },
    iphone_se: { w: 375, h: 667, label: 'iPhone SE' },
    ipad: { w: 820, h: 1180, label: 'iPad' },
  }

  const device = DEVICE_SIZES[deviceFrame]
  const selectedId = selectedIds.size === 1 ? Array.from(selectedIds)[0] : null
  const selected = selectedId ? nodes.find(n => n.id === selectedId) || null : null

  // Root-level nodes (no parent)
  const rootIds = nodes.filter(n => !n.parentId).map(n => n.id)

  // ─── History management ─────────────────────────────────────────
  const pushHistory = useCallback((newNodes: DesignNode[], newSelectedIds: Set<string>) => {
    if (isUndoRedoRef.current) { isUndoRedoRef.current = false; return }
    setHistory(prev => {
      const truncated = prev.slice(0, historyIndex + 1)
      const entry: HistoryEntry = { nodes: newNodes.map(n => ({ ...n, props: { ...n.props }, children: [...n.children] })), selectedIds: new Set(newSelectedIds) }
      const next = [...truncated, entry]
      if (next.length > 100) next.shift()
      return next
    })
    setHistoryIndex(prev => prev + 1)
  }, [historyIndex])

  // Track node changes for history (skip during drag for perf)
  const prevNodesRef = useRef<string>('')
  useEffect(() => {
    if (dragState) return
    const sig = JSON.stringify(nodes)
    if (sig !== prevNodesRef.current) {
      prevNodesRef.current = sig
      pushHistory(nodes, selectedIds)
    }
  }, [nodes, selectedIds, dragState, pushHistory])

  function undo() {
    if (historyIndex <= 0) return
    const prev = history[historyIndex - 1]
    if (!prev) return
    isUndoRedoRef.current = true
    setHistoryIndex(i => i - 1)
    setNodes(prev.nodes.map(n => ({ ...n, props: { ...n.props }, children: [...n.children] })))
    setSelectedIds(new Set(prev.selectedIds))
  }

  function redo() {
    if (historyIndex >= history.length - 1) return
    const next = history[historyIndex + 1]
    if (!next) return
    isUndoRedoRef.current = true
    setHistoryIndex(i => i + 1)
    setNodes(next.nodes.map(n => ({ ...n, props: { ...n.props }, children: [...n.children] })))
    setSelectedIds(new Set(next.selectedIds))
  }

  // ─── Auto-save to localStorage ──────────────────────────────────
  useEffect(() => {
    try { localStorage.setItem(AUTOSAVE_KEY, JSON.stringify(nodes)) } catch {}
  }, [nodes])

  // Load autosave on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem(AUTOSAVE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (Array.isArray(parsed) && parsed.length > 0) setNodes(parsed)
      }
    } catch {}
  }, [])

  // ─── Save/Load ──────────────────────────────────────────────────
  function saveDesign() {
    const name = `Design ${new Date().toLocaleString()}`
    const designs = loadSavedDesigns()
    designs.push({ name, timestamp: Date.now(), nodes: nodes.map(n => ({ ...n, props: { ...n.props }, children: [...n.children] })) })
    saveSavedDesigns(designs)
  }

  function loadDesign(loadedNodes: DesignNode[]) {
    setNodes(loadedNodes)
    setSelectedIds(new Set())
  }

  // ─── Node operations ───────────────────────────────────────────
  function addNode(type: SwiftComponent, w: number, h: number) {
    const id = uid()
    const newNode: DesignNode = {
      id,
      type,
      x: Math.round(device.w / 2 - w / 2),
      y: Math.round(device.h / 3),
      w,
      h,
      props: { ...DEFAULT_PROPS[type] },
      children: [],
    }
    setNodes(prev => [...prev, newNode])
    setSelectedIds(new Set([id]))
  }

  function updateProps(id: string, props: Record<string, string | number | boolean>) {
    setNodes(prev => prev.map(n => {
      if (n.id !== id) return n
      const { __x, __y, __w, __h, ...rest } = props as any
      return {
        ...n,
        x: __x !== undefined ? __x : n.x,
        y: __y !== undefined ? __y : n.y,
        w: __w !== undefined ? __w : n.w,
        h: __h !== undefined ? __h : n.h,
        props: rest,
      }
    }))
  }

  function deleteSelected() {
    if (selectedIds.size === 0) return
    setNodes(prev => prev.filter(n => !selectedIds.has(n.id)))
    setSelectedIds(new Set())
  }

  function deleteNode(id: string) {
    setNodes(prev => prev.filter(n => n.id !== id))
    setSelectedIds(prev => { const s = new Set(prev); s.delete(id); return s })
  }

  function duplicateSelected() {
    if (selectedIds.size === 0) return
    const newIds: string[] = []
    setNodes(prev => {
      const toClone = prev.filter(n => selectedIds.has(n.id))
      const clones = toClone.map(n => {
        const c = cloneNode(n)
        newIds.push(c.id)
        return c
      })
      return [...prev, ...clones]
    })
    setTimeout(() => setSelectedIds(new Set(newIds)), 0)
  }

  // ─── Layer ordering ─────────────────────────────────────────────
  function bringForward() {
    if (selectedIds.size === 0) return
    setNodes(prev => {
      const next = [...prev]
      for (let i = next.length - 2; i >= 0; i--) {
        if (selectedIds.has(next[i].id) && !selectedIds.has(next[i + 1].id)) {
          ;[next[i], next[i + 1]] = [next[i + 1], next[i]]
        }
      }
      return next
    })
  }

  function sendBackward() {
    if (selectedIds.size === 0) return
    setNodes(prev => {
      const next = [...prev]
      for (let i = 1; i < next.length; i++) {
        if (selectedIds.has(next[i].id) && !selectedIds.has(next[i - 1].id)) {
          ;[next[i], next[i - 1]] = [next[i - 1], next[i]]
        }
      }
      return next
    })
  }

  // ─── Drag (supports multi-select) ──────────────────────────────
  function handleDragStart(id: string, e: React.MouseEvent) {
    if (!canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    const dragIds = selectedIds.has(id) ? Array.from(selectedIds) : [id]
    const offsets = new Map<string, { ox: number; oy: number }>()
    for (const did of dragIds) {
      const node = nodes.find(n => n.id === did)
      if (node) offsets.set(did, { ox: e.clientX - rect.left - node.x, oy: e.clientY - rect.top - node.y })
    }
    setDragState({ ids: dragIds, offsets })
  }

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!dragState || !canvasRef.current) return
    const rect = canvasRef.current.getBoundingClientRect()
    setNodes(prev => prev.map(n => {
      const off = dragState.offsets.get(n.id)
      if (!off) return n
      let x = Math.round(e.clientX - rect.left - off.ox)
      let y = Math.round(e.clientY - rect.top - off.oy)
      if (snapEnabled) { x = snapToGrid(x); y = snapToGrid(y) }
      return { ...n, x, y }
    }))
  }, [dragState, snapEnabled])

  const handleMouseUp = useCallback(() => {
    if (dragState) setDragState(null)
  }, [dragState])

  useEffect(() => {
    if (dragState) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => { window.removeEventListener('mousemove', handleMouseMove); window.removeEventListener('mouseup', handleMouseUp) }
    }
  }, [dragState, handleMouseMove, handleMouseUp])

  const swiftCode = generateSwiftUI(nodes, rootIds)

  function copyCode() {
    navigator.clipboard.writeText(swiftCode)
  }

  // ─── Selection handler ──────────────────────────────────────────
  function handleSelect(id: string, e: React.MouseEvent) {
    if (e.shiftKey) {
      setSelectedIds(prev => {
        const next = new Set(prev)
        if (next.has(id)) next.delete(id)
        else next.add(id)
        return next
      })
    } else {
      setSelectedIds(new Set([id]))
    }
  }

  // ─── Keyboard shortcuts ─────────────────────────────────────────
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      const isInput = document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'SELECT' || document.activeElement?.tagName === 'TEXTAREA'
      if (isInput) return

      const meta = e.metaKey || e.ctrlKey

      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedIds.size > 0) { e.preventDefault(); deleteSelected() }
      }
      if (e.key === 'Escape') setSelectedIds(new Set())
      if (meta && e.key === 'z' && !e.shiftKey) { e.preventDefault(); undo() }
      if (meta && e.key === 'z' && e.shiftKey) { e.preventDefault(); redo() }
      if (meta && e.key === 'd') { e.preventDefault(); duplicateSelected() }
      if (meta && e.key === ']') { e.preventDefault(); bringForward() }
      if (meta && e.key === '[') { e.preventDefault(); sendBackward() }
      if (meta && e.key === 's') { e.preventDefault(); saveDesign() }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  })

  const tbSep = <div style={{ width: 1, height: 20, background: '#334155' }} />

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0f172a', color: '#e2e8f0', fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro", sans-serif' }}>

      {showSaveLoad && <SaveLoadModal onClose={() => setShowSaveLoad(false)} onLoad={loadDesign} />}

      {/* Left: Component Palette */}
      <div style={{ width: 200, borderRight: '1px solid #1e293b', padding: 12, overflowY: 'auto', flexShrink: 0 }}>
        <Link href="/cc" style={{ fontSize: 11, color: '#64748b', textDecoration: 'none' }}>← Core</Link>
        <h2 style={{ fontSize: 15, fontWeight: 700, margin: '8px 0 12px', color: '#f8fafc' }}>Design</h2>
        <div style={{ fontSize: 10, color: '#64748b', marginBottom: 12 }}>by timelabs — free for all</div>

        {COMPONENT_PALETTE.map(group => (
          <div key={group.label} style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, color: '#64748b', marginBottom: 6 }}>{group.label}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {group.items.map(item => (
                <button
                  key={item.type}
                  onClick={() => addNode(item.type, item.w, item.h)}
                  style={{
                    padding: '4px 8px', background: '#1e293b', border: '1px solid #334155', borderRadius: 4,
                    color: '#e2e8f0', fontSize: 11, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4,
                  }}
                  title={item.type}
                >
                  <span style={{ fontSize: 13 }}>{item.icon}</span>
                  <span>{item.type}</span>
                </button>
              ))}
            </div>
          </div>
        ))}

        <div style={{ marginTop: 16, borderTop: '1px solid #1e293b', paddingTop: 12 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, color: '#64748b', marginBottom: 6 }}>Device</div>
          <select
            value={deviceFrame}
            onChange={e => setDeviceFrame(e.target.value as any)}
            style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', borderRadius: 4, padding: '4px 6px', color: '#e2e8f0', fontSize: 12 }}
          >
            {Object.entries(DEVICE_SIZES).map(([key, v]) => <option key={key} value={key}>{v.label} ({v.w}×{v.h})</option>)}
          </select>
        </div>

        {/* Layer list */}
        <div style={{ marginTop: 16, borderTop: '1px solid #1e293b', paddingTop: 12 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, color: '#64748b', marginBottom: 6 }}>Layers</div>
          {nodes.length === 0 && <div style={{ fontSize: 11, color: '#475569' }}>No layers</div>}
          {[...nodes].reverse().map((n, ri) => {
            const zIdx = nodes.length - 1 - ri
            return (
              <div
                key={n.id}
                onClick={(e) => handleSelect(n.id, e as any)}
                style={{
                  padding: '3px 6px', marginBottom: 2, borderRadius: 4, fontSize: 11, cursor: 'pointer',
                  background: selectedIds.has(n.id) ? '#1e3a5f' : 'transparent',
                  color: selectedIds.has(n.id) ? '#60a5fa' : '#94a3b8',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}
              >
                <span>{n.type}</span>
                <span style={{ fontSize: 9, color: '#475569' }}>z{zIdx}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Center: Canvas */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Toolbar */}
        <div style={{ height: 40, borderBottom: '1px solid #1e293b', display: 'flex', alignItems: 'center', padding: '0 8px', gap: 4 }}>
          <ToolBtn icon="↩" onClick={undo} disabled={historyIndex <= 0} tooltip="Undo (Cmd+Z)" />
          <ToolBtn icon="↪" onClick={redo} disabled={historyIndex >= history.length - 1} tooltip="Redo (Cmd+Shift+Z)" />
          {tbSep}
          <ToolBtn icon="⊞" label="Save" onClick={saveDesign} tooltip="Save design (Cmd+S)" />
          <ToolBtn icon="⊟" label="Load" onClick={() => setShowSaveLoad(true)} tooltip="Load saved design" />
          {tbSep}
          <ToolBtn icon="⊡" onClick={() => setSnapEnabled(!snapEnabled)} active={snapEnabled} tooltip={`Snap to ${GRID_SIZE}px grid (${snapEnabled ? 'ON' : 'OFF'})`} label="Snap" />
          {tbSep}
          <ToolBtn icon="⧉" onClick={duplicateSelected} disabled={selectedIds.size === 0} tooltip="Duplicate (Cmd+D)" />
          <ToolBtn icon="⬆" onClick={bringForward} disabled={selectedIds.size === 0} tooltip="Bring forward (Cmd+])" />
          <ToolBtn icon="⬇" onClick={sendBackward} disabled={selectedIds.size === 0} tooltip="Send backward (Cmd+[)" />
          <ToolBtn icon="✕" onClick={deleteSelected} disabled={selectedIds.size === 0} tooltip="Delete (Del)" />
          {tbSep}
          <button onClick={() => setShowCode(!showCode)} style={{ padding: '4px 12px', background: showCode ? '#007AFF' : '#1e293b', border: '1px solid #334155', borderRadius: 4, color: '#e2e8f0', fontSize: 12, cursor: 'pointer' }}>
            {showCode ? '← Canvas' : 'SwiftUI Code'}
          </button>
          {showCode && (
            <button onClick={copyCode} style={{ padding: '4px 12px', background: '#1e293b', border: '1px solid #334155', borderRadius: 4, color: '#e2e8f0', fontSize: 12, cursor: 'pointer' }}>Copy</button>
          )}
          <div style={{ flex: 1 }} />
          {selectedIds.size > 1 && <span style={{ fontSize: 11, color: '#60a5fa' }}>{selectedIds.size} selected</span>}
          <span style={{ fontSize: 11, color: '#64748b' }}>{nodes.length} component{nodes.length !== 1 ? 's' : ''}</span>
        </div>

        {/* Canvas or Code */}
        <div style={{ flex: 1, overflow: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0a0f1a' }}>
          {showCode ? (
            <pre style={{ width: '100%', maxWidth: 700, padding: 24, margin: 24, background: '#1e293b', borderRadius: 12, fontSize: 13, lineHeight: 1.5, color: '#e2e8f0', whiteSpace: 'pre-wrap', overflowY: 'auto', maxHeight: '80vh' }}>
              {swiftCode}
            </pre>
          ) : (
            <div style={{ position: 'relative' }}>
              {/* iPhone frame */}
              <div style={{
                width: device.w + 24,
                height: device.h + 80,
                background: '#1a1a2e',
                borderRadius: 44,
                border: '3px solid #334155',
                padding: '40px 12px',
                boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
              }}>
                {/* Status bar */}
                <div style={{ height: 20, display: 'flex', justifyContent: 'center', marginBottom: 4 }}>
                  <div style={{ width: 100, height: 6, borderRadius: 3, background: '#334155' }} />
                </div>
                {/* Canvas area */}
                <div
                  ref={canvasRef}
                  onClick={() => setSelectedIds(new Set())}
                  style={{
                    position: 'relative',
                    width: device.w,
                    height: device.h - 44,
                    background: '#ffffff',
                    borderRadius: 4,
                    overflow: 'hidden',
                  }}
                >
                  {/* Grid overlay */}
                  {snapEnabled && (
                    <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 0, opacity: 0.15 }}>
                      <defs>
                        <pattern id="grid8" width={GRID_SIZE} height={GRID_SIZE} patternUnits="userSpaceOnUse">
                          <path d={`M ${GRID_SIZE} 0 L 0 0 0 ${GRID_SIZE}`} fill="none" stroke="#007AFF" strokeWidth="0.5" />
                        </pattern>
                      </defs>
                      <rect width="100%" height="100%" fill="url(#grid8)" />
                    </svg>
                  )}
                  {nodes.map((node, idx) => (
                    <NodeRenderer
                      key={node.id}
                      node={node}
                      selected={selectedIds.has(node.id)}
                      onSelect={(e) => handleSelect(node.id, e)}
                      onDragStart={(e) => handleDragStart(node.id, e)}
                      zIndex={idx + 1}
                    />
                  ))}
                  {nodes.length === 0 && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
                      <div style={{ fontSize: 32, marginBottom: 8 }}>⬜</div>
                      <div style={{ fontSize: 14 }}>Drag components from the palette</div>
                      <div style={{ fontSize: 12, marginTop: 4, color: '#64748b' }}>or click any component to add it</div>
                    </div>
                  )}
                </div>
                {/* Home indicator */}
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: 8 }}>
                  <div style={{ width: 120, height: 4, borderRadius: 2, background: '#334155' }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Right: Inspector */}
      <div style={{ width: 220, borderLeft: '1px solid #1e293b', padding: 12, overflowY: 'auto', flexShrink: 0 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: '#f8fafc', margin: '0 0 12px' }}>Inspector</h3>
        {selected ? (
          <Inspector node={selected} onChange={updateProps} onDelete={deleteNode} />
        ) : selectedIds.size > 1 ? (
          <div style={{ fontSize: 12, color: '#60a5fa' }}>{selectedIds.size} components selected. Use toolbar to move, duplicate, or delete.</div>
        ) : (
          <div style={{ fontSize: 12, color: '#64748b' }}>Select a component to edit its properties</div>
        )}

        {/* Keyboard shortcuts reference */}
        <div style={{ marginTop: 24, borderTop: '1px solid #1e293b', paddingTop: 12 }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: 1, color: '#64748b', marginBottom: 8 }}>Shortcuts</div>
          {[
            ['Cmd+Z', 'Undo'],
            ['Cmd+Shift+Z', 'Redo'],
            ['Cmd+D', 'Duplicate'],
            ['Cmd+S', 'Save'],
            ['Cmd+]', 'Bring forward'],
            ['Cmd+[', 'Send backward'],
            ['Shift+Click', 'Multi-select'],
            ['Del', 'Delete'],
            ['Esc', 'Deselect'],
          ].map(([key, desc]) => (
            <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#64748b', marginBottom: 3 }}>
              <span style={{ color: '#94a3b8', fontFamily: 'monospace' }}>{key}</span>
              <span>{desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
