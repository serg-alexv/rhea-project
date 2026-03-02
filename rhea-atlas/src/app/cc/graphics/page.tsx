'use client'

import { useRef, useState, useCallback, useEffect } from 'react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_CC_API ?? 'http://localhost:8400'

// ─── Types ───────────────────────────────────────────────────────────

type ShapeKind = 'rect' | 'ellipse' | 'line' | 'arrow' | 'text' | 'path' | 'image'
type ToolMode = 'select' | ShapeKind

interface Vec2 { x: number; y: number }

interface GShape {
  id: string
  kind: ShapeKind
  x: number; y: number
  w: number; h: number
  fill: string
  stroke: string
  strokeWidth: number
  opacity: number
  rotation: number
  text?: string
  fontSize?: number
  fontFamily?: string
  points?: Vec2[]        // freehand path
  imageData?: string     // data URL for images
  locked?: boolean
}

// ─── Helpers ─────────────────────────────────────────────────────────

const uid = () => Math.random().toString(36).slice(2, 10)
const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v))

const COLORS = [
  '#ffffff', '#ef4444', '#f97316', '#eab308', '#22c55e',
  '#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899', '#000000',
  '#1e293b', '#334155', '#64748b', '#94a3b8', '#cbd5e1',
]

const DEFAULT_SHAPE: Partial<GShape> = {
  fill: 'transparent',
  stroke: '#3b82f6',
  strokeWidth: 2,
  opacity: 1,
  rotation: 0,
}

// ─── SVG Shape Renderer ─────────────────────────────────────────────

function ShapeSVG({ shape, selected, onMouseDown }: {
  shape: GShape
  selected: boolean
  onMouseDown: (e: React.MouseEvent) => void
}) {
  const common = {
    onMouseDown,
    style: { cursor: 'move', opacity: shape.opacity },
    transform: `rotate(${shape.rotation} ${shape.x + shape.w / 2} ${shape.y + shape.h / 2})`,
  }
  const sel = selected ? { filter: 'url(#sel-glow)' } : {}

  switch (shape.kind) {
    case 'rect':
      return <rect x={shape.x} y={shape.y} width={shape.w} height={shape.h}
        fill={shape.fill} stroke={shape.stroke} strokeWidth={shape.strokeWidth}
        rx={4} {...common} {...sel} />
    case 'ellipse':
      return <ellipse cx={shape.x + shape.w / 2} cy={shape.y + shape.h / 2}
        rx={shape.w / 2} ry={shape.h / 2}
        fill={shape.fill} stroke={shape.stroke} strokeWidth={shape.strokeWidth}
        {...common} {...sel} />
    case 'line':
      return <line x1={shape.x} y1={shape.y} x2={shape.x + shape.w} y2={shape.y + shape.h}
        stroke={shape.stroke} strokeWidth={shape.strokeWidth}
        {...common} {...sel} />
    case 'arrow': {
      const x2 = shape.x + shape.w, y2 = shape.y + shape.h
      const angle = Math.atan2(shape.h, shape.w)
      const hl = 14
      const a1x = x2 - hl * Math.cos(angle - 0.4), a1y = y2 - hl * Math.sin(angle - 0.4)
      const a2x = x2 - hl * Math.cos(angle + 0.4), a2y = y2 - hl * Math.sin(angle + 0.4)
      return <g {...common} {...sel}>
        <line x1={shape.x} y1={shape.y} x2={x2} y2={y2}
          stroke={shape.stroke} strokeWidth={shape.strokeWidth} />
        <polygon points={`${x2},${y2} ${a1x},${a1y} ${a2x},${a2y}`}
          fill={shape.stroke} />
      </g>
    }
    case 'text':
      return <text x={shape.x} y={shape.y + (shape.fontSize ?? 18)}
        fill={shape.fill === 'transparent' ? shape.stroke : shape.fill}
        fontSize={shape.fontSize ?? 18}
        fontFamily={shape.fontFamily ?? 'monospace'}
        {...common} {...sel}>
        {shape.text ?? 'Text'}
      </text>
    case 'path':
      if (!shape.points?.length) return null
      const d = shape.points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
      return <path d={d} fill="none" stroke={shape.stroke}
        strokeWidth={shape.strokeWidth} strokeLinecap="round" strokeLinejoin="round"
        {...common} {...sel} />
    case 'image':
      return shape.imageData ? <image href={shape.imageData} x={shape.x} y={shape.y}
        width={shape.w} height={shape.h} {...common} {...sel} /> : null
    default:
      return null
  }
}

// ─── Selection Handles ──────────────────────────────────────────────

function SelectionHandles({ shape, onResize }: {
  shape: GShape
  onResize: (corner: string, e: React.MouseEvent) => void
}) {
  const corners = [
    { id: 'nw', x: shape.x, y: shape.y },
    { id: 'ne', x: shape.x + shape.w, y: shape.y },
    { id: 'sw', x: shape.x, y: shape.y + shape.h },
    { id: 'se', x: shape.x + shape.w, y: shape.y + shape.h },
  ]
  return <>
    <rect x={shape.x - 1} y={shape.y - 1} width={shape.w + 2} height={shape.h + 2}
      fill="none" stroke="#06b6d4" strokeWidth={1} strokeDasharray="4 2" />
    {corners.map(c =>
      <rect key={c.id} x={c.x - 4} y={c.y - 4} width={8} height={8}
        fill="#06b6d4" stroke="#0f0f1a" strokeWidth={1} rx={1}
        style={{ cursor: `${c.id}-resize` }}
        onMouseDown={e => { e.stopPropagation(); onResize(c.id, e) }} />
    )}
  </>
}

// ─── Property Panel ─────────────────────────────────────────────────

function PropPanel({ shape, onChange }: {
  shape: GShape
  onChange: (patch: Partial<GShape>) => void
}) {
  return (
    <div className="space-y-3 text-xs">
      <div className="text-white/60 font-medium uppercase tracking-wider">Properties</div>

      {/* Position */}
      <div className="grid grid-cols-2 gap-2">
        <label className="text-white/40">X
          <input type="number" value={Math.round(shape.x)} onChange={e => onChange({ x: +e.target.value })}
            className="w-full mt-0.5 bg-white/5 border border-white/10 rounded px-2 py-1 text-white" />
        </label>
        <label className="text-white/40">Y
          <input type="number" value={Math.round(shape.y)} onChange={e => onChange({ y: +e.target.value })}
            className="w-full mt-0.5 bg-white/5 border border-white/10 rounded px-2 py-1 text-white" />
        </label>
        <label className="text-white/40">W
          <input type="number" value={Math.round(shape.w)} onChange={e => onChange({ w: +e.target.value })}
            className="w-full mt-0.5 bg-white/5 border border-white/10 rounded px-2 py-1 text-white" />
        </label>
        <label className="text-white/40">H
          <input type="number" value={Math.round(shape.h)} onChange={e => onChange({ h: +e.target.value })}
            className="w-full mt-0.5 bg-white/5 border border-white/10 rounded px-2 py-1 text-white" />
        </label>
      </div>

      {/* Fill color */}
      <div>
        <div className="text-white/40 mb-1">Fill</div>
        <div className="flex flex-wrap gap-1">
          <button onClick={() => onChange({ fill: 'transparent' })}
            className={`w-5 h-5 rounded border ${shape.fill === 'transparent' ? 'border-cyan-400' : 'border-white/20'}`}
            style={{ background: 'repeating-conic-gradient(#333 0% 25%, #555 0% 50%) 50% / 8px 8px' }} />
          {COLORS.map(c =>
            <button key={c} onClick={() => onChange({ fill: c })}
              className={`w-5 h-5 rounded border ${shape.fill === c ? 'border-cyan-400' : 'border-white/20'}`}
              style={{ background: c }} />
          )}
        </div>
      </div>

      {/* Stroke color */}
      <div>
        <div className="text-white/40 mb-1">Stroke</div>
        <div className="flex flex-wrap gap-1">
          {COLORS.map(c =>
            <button key={c} onClick={() => onChange({ stroke: c })}
              className={`w-5 h-5 rounded border ${shape.stroke === c ? 'border-cyan-400' : 'border-white/20'}`}
              style={{ background: c }} />
          )}
        </div>
      </div>

      {/* Stroke width */}
      <label className="text-white/40 block">
        Stroke width: {shape.strokeWidth}
        <input type="range" min={0} max={12} step={0.5} value={shape.strokeWidth}
          onChange={e => onChange({ strokeWidth: +e.target.value })}
          className="w-full mt-1 accent-cyan-500" />
      </label>

      {/* Opacity */}
      <label className="text-white/40 block">
        Opacity: {Math.round(shape.opacity * 100)}%
        <input type="range" min={0} max={1} step={0.05} value={shape.opacity}
          onChange={e => onChange({ opacity: +e.target.value })}
          className="w-full mt-1 accent-cyan-500" />
      </label>

      {/* Rotation */}
      <label className="text-white/40 block">
        Rotation: {shape.rotation}°
        <input type="range" min={0} max={360} step={1} value={shape.rotation}
          onChange={e => onChange({ rotation: +e.target.value })}
          className="w-full mt-1 accent-cyan-500" />
      </label>

      {/* Text props */}
      {shape.kind === 'text' && (
        <>
          <label className="text-white/40 block">
            Text
            <input type="text" value={shape.text ?? ''} onChange={e => onChange({ text: e.target.value })}
              className="w-full mt-0.5 bg-white/5 border border-white/10 rounded px-2 py-1 text-white" />
          </label>
          <label className="text-white/40 block">
            Font size: {shape.fontSize ?? 18}
            <input type="range" min={8} max={72} value={shape.fontSize ?? 18}
              onChange={e => onChange({ fontSize: +e.target.value })}
              className="w-full mt-1 accent-cyan-500" />
          </label>
        </>
      )}
    </div>
  )
}

// ─── Layers Panel ───────────────────────────────────────────────────

function LayersPanel({ shapes, selectedId, onSelect, onReorder, onDelete }: {
  shapes: GShape[]
  selectedId: string | null
  onSelect: (id: string) => void
  onReorder: (id: string, dir: 'up' | 'down') => void
  onDelete: (id: string) => void
}) {
  return (
    <div className="space-y-1">
      <div className="text-white/60 text-xs font-medium uppercase tracking-wider mb-2">Layers</div>
      {[...shapes].reverse().map((s, i) => (
        <div key={s.id}
          onClick={() => onSelect(s.id)}
          className={`flex items-center gap-2 px-2 py-1 rounded text-xs cursor-pointer
            ${selectedId === s.id ? 'bg-cyan-500/20 text-cyan-300' : 'text-white/50 hover:bg-white/5'}`}>
          <span className="w-3 h-3 rounded-sm border border-white/20" style={{
            background: s.fill === 'transparent' ? s.stroke : s.fill
          }} />
          <span className="flex-1 truncate">{s.kind}{s.text ? `: ${s.text}` : ''}</span>
          <button onClick={e => { e.stopPropagation(); onReorder(s.id, 'up') }}
            className="text-white/30 hover:text-white/70">↑</button>
          <button onClick={e => { e.stopPropagation(); onReorder(s.id, 'down') }}
            className="text-white/30 hover:text-white/70">↓</button>
          <button onClick={e => { e.stopPropagation(); onDelete(s.id) }}
            className="text-white/30 hover:text-red-400">×</button>
        </div>
      ))}
      {shapes.length === 0 && <div className="text-white/20 text-xs italic">No shapes yet</div>}
    </div>
  )
}

// ─── Tribunal Integration ───────────────────────────────────────────

function TribunalPanel({ svgRef, shapes }: { svgRef: React.RefObject<SVGSVGElement | null>; shapes: GShape[] }) {
  const [claim, setClaim] = useState('')
  const [result, setResult] = useState<{ agreement: number; confidence: number; text: string } | null>(null)
  const [loading, setLoading] = useState(false)

  const evaluate = async () => {
    if (!claim.trim()) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/tribunal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: claim, k: 3, tier: 'cheap' }),
      })
      const data = await res.json()
      setResult({
        agreement: data.agreement_score ?? 0,
        confidence: data.confidence ?? 0,
        text: data.response ?? data.answer ?? '',
      })
    } catch { setResult(null) }
    setLoading(false)
  }

  return (
    <div className="space-y-2">
      <div className="text-white/60 text-xs font-medium uppercase tracking-wider">Tribunal</div>
      <textarea value={claim} onChange={e => setClaim(e.target.value)}
        placeholder="Describe your diagram for consensus evaluation..."
        className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs text-white resize-none h-16" />
      <button onClick={evaluate} disabled={loading}
        className="w-full py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white text-xs rounded font-medium">
        {loading ? 'Evaluating...' : 'Evaluate Diagram'}
      </button>
      {result && (
        <div className="bg-white/5 rounded p-2 text-xs space-y-1">
          <div className="flex justify-between">
            <span className="text-white/40">Agreement</span>
            <span className={result.agreement > 0.7 ? 'text-green-400' : result.agreement > 0.4 ? 'text-yellow-400' : 'text-red-400'}>
              {Math.round(result.agreement * 100)}%
            </span>
          </div>
          <div className="text-white/60 mt-1">{result.text.slice(0, 200)}</div>
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════

export default function GraphicsPage() {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [shapes, setShapes] = useState<GShape[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [tool, setTool] = useState<ToolMode>('select')
  const [drawing, setDrawing] = useState(false)
  const [drawStart, setDrawStart] = useState<Vec2 | null>(null)
  const [dragOffset, setDragOffset] = useState<Vec2 | null>(null)
  const [resizeCorner, setResizeCorner] = useState<string | null>(null)
  const [resizeStart, setResizeStart] = useState<{ corner: string; mx: number; my: number; shape: GShape } | null>(null)
  const [canvasSize] = useState({ w: 1200, h: 800 })
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState<Vec2>({ x: 0, y: 0 })
  const [currentFill, setCurrentFill] = useState('transparent')
  const [currentStroke, setCurrentStroke] = useState('#3b82f6')
  const [currentStrokeWidth, setCurrentStrokeWidth] = useState(2)
  const [showGrid, setShowGrid] = useState(true)

  const selected = shapes.find(s => s.id === selectedId) ?? null

  // ─── SVG coordinate transform ──────────────────────────────────
  const screenToSVG = useCallback((clientX: number, clientY: number): Vec2 => {
    const svg = svgRef.current
    if (!svg) return { x: clientX, y: clientY }
    const rect = svg.getBoundingClientRect()
    return {
      x: (clientX - rect.left) / zoom - pan.x,
      y: (clientY - rect.top) / zoom - pan.y,
    }
  }, [zoom, pan])

  // ─── Shape CRUD ────────────────────────────────────────────────
  const updateShape = useCallback((id: string, patch: Partial<GShape>) => {
    setShapes(prev => prev.map(s => s.id === id ? { ...s, ...patch } : s))
  }, [])

  const addShape = useCallback((kind: ShapeKind, x: number, y: number, w: number, h: number): GShape => {
    const shape: GShape = {
      id: uid(), kind, x, y, w, h,
      fill: currentFill, stroke: currentStroke,
      strokeWidth: currentStrokeWidth, opacity: 1, rotation: 0,
      ...(kind === 'text' ? { text: 'Text', fontSize: 18, fontFamily: 'monospace' } : {}),
    }
    setShapes(prev => [...prev, shape])
    setSelectedId(shape.id)
    return shape
  }, [currentFill, currentStroke, currentStrokeWidth])

  const deleteShape = useCallback((id: string) => {
    setShapes(prev => prev.filter(s => s.id !== id))
    if (selectedId === id) setSelectedId(null)
  }, [selectedId])

  const reorderShape = useCallback((id: string, dir: 'up' | 'down') => {
    setShapes(prev => {
      const idx = prev.findIndex(s => s.id === id)
      if (idx < 0) return prev
      const next = [...prev]
      const swap = dir === 'up' ? idx + 1 : idx - 1
      if (swap < 0 || swap >= next.length) return prev
      ;[next[idx], next[swap]] = [next[swap], next[idx]]
      return next
    })
  }, [])

  // ─── Mouse handlers ───────────────────────────────────────────
  const onCanvasMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return
    const pt = screenToSVG(e.clientX, e.clientY)

    if (tool === 'select') {
      // clicked on empty space
      setSelectedId(null)
      return
    }

    if (tool === 'path') {
      const shape: GShape = {
        id: uid(), kind: 'path', x: 0, y: 0, w: 0, h: 0,
        fill: 'transparent', stroke: currentStroke,
        strokeWidth: currentStrokeWidth, opacity: 1, rotation: 0,
        points: [pt],
      }
      setShapes(prev => [...prev, shape])
      setSelectedId(shape.id)
      setDrawing(true)
      return
    }

    setDrawStart(pt)
    setDrawing(true)
  }, [tool, screenToSVG, currentStroke, currentStrokeWidth])

  const onCanvasMouseMove = useCallback((e: React.MouseEvent) => {
    const pt = screenToSVG(e.clientX, e.clientY)

    // Freehand path drawing
    if (drawing && tool === 'path' && selectedId) {
      setShapes(prev => prev.map(s => {
        if (s.id !== selectedId || !s.points) return s
        return { ...s, points: [...s.points, pt] }
      }))
      return
    }

    // Shape drawing
    if (drawing && drawStart && tool !== 'select' && tool !== 'path') {
      const existing = shapes.find(s => s.id === selectedId && s.kind === tool)
      const x = Math.min(drawStart.x, pt.x)
      const y = Math.min(drawStart.y, pt.y)
      const w = Math.abs(pt.x - drawStart.x)
      const h = Math.abs(pt.y - drawStart.y)

      if (tool === 'line' || tool === 'arrow') {
        if (existing) {
          updateShape(existing.id, { w: pt.x - drawStart.x, h: pt.y - drawStart.y })
        } else {
          addShape(tool, drawStart.x, drawStart.y, pt.x - drawStart.x, pt.y - drawStart.y)
        }
      } else {
        if (existing) {
          updateShape(existing.id, { x, y, w, h })
        } else {
          addShape(tool, x, y, w, h)
        }
      }
      return
    }

    // Dragging selected shape
    if (dragOffset && selectedId) {
      updateShape(selectedId, { x: pt.x - dragOffset.x, y: pt.y - dragOffset.y })
      return
    }

    // Resizing
    if (resizeStart && selectedId) {
      const dx = pt.x - resizeStart.mx
      const dy = pt.y - resizeStart.my
      const s = resizeStart.shape
      let { x, y, w, h } = s
      const corner = resizeStart.corner
      if (corner.includes('e')) { w = Math.max(10, s.w + (pt.x - resizeStart.mx)) }
      if (corner.includes('w')) { x = s.x + (pt.x - resizeStart.mx); w = Math.max(10, s.w - (pt.x - resizeStart.mx)) }
      if (corner.includes('s')) { h = Math.max(10, s.h + (pt.y - resizeStart.my)) }
      if (corner.includes('n')) { y = s.y + (pt.y - resizeStart.my); h = Math.max(10, s.h - (pt.y - resizeStart.my)) }
      updateShape(selectedId, { x, y, w, h })
    }
  }, [drawing, drawStart, tool, selectedId, shapes, screenToSVG, dragOffset, resizeStart, updateShape, addShape])

  const onCanvasMouseUp = useCallback(() => {
    setDrawing(false)
    setDrawStart(null)
    setDragOffset(null)
    setResizeStart(null)
  }, [])

  const onShapeMouseDown = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (tool !== 'select') return
    setSelectedId(id)
    const pt = screenToSVG(e.clientX, e.clientY)
    const shape = shapes.find(s => s.id === id)
    if (shape) {
      setDragOffset({ x: pt.x - shape.x, y: pt.y - shape.y })
    }
  }, [tool, shapes, screenToSVG])

  const onResize = useCallback((corner: string, e: React.MouseEvent) => {
    if (!selected) return
    const pt = screenToSVG(e.clientX, e.clientY)
    setResizeStart({ corner, mx: pt.x, my: pt.y, shape: { ...selected } })
  }, [selected, screenToSVG])

  // ─── Keyboard shortcuts ───────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === 'INPUT' || (e.target as HTMLElement).tagName === 'TEXTAREA') return
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedId) deleteShape(selectedId)
      }
      if (e.key === 'v') setTool('select')
      if (e.key === 'r') setTool('rect')
      if (e.key === 'e') setTool('ellipse')
      if (e.key === 'l') setTool('line')
      if (e.key === 'a') setTool('arrow')
      if (e.key === 't') setTool('text')
      if (e.key === 'p') setTool('path')
      if (e.key === 'Escape') { setSelectedId(null); setTool('select') }
      if ((e.metaKey || e.ctrlKey) && e.key === 'd' && selectedId) {
        e.preventDefault()
        const src = shapes.find(s => s.id === selectedId)
        if (src) {
          const dup = { ...src, id: uid(), x: src.x + 20, y: src.y + 20 }
          setShapes(prev => [...prev, dup])
          setSelectedId(dup.id)
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [selectedId, shapes, deleteShape])

  // ─── Export ────────────────────────────────────────────────────
  const exportSVG = useCallback(() => {
    const svg = svgRef.current
    if (!svg) return
    // Clone SVG, remove selection effects
    const clone = svg.cloneNode(true) as SVGSVGElement
    clone.removeAttribute('style')
    clone.setAttribute('width', String(canvasSize.w))
    clone.setAttribute('height', String(canvasSize.h))
    // Remove grid
    const grid = clone.querySelector('#editor-grid')
    grid?.remove()
    // Remove selection handles
    clone.querySelectorAll('[data-sel-handle]').forEach(el => el.remove())

    const xml = new XMLSerializer().serializeToString(clone)
    const blob = new Blob([xml], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'rhea-graphic.svg'; a.click()
    URL.revokeObjectURL(url)
  }, [canvasSize])

  const exportPNG = useCallback(() => {
    const svg = svgRef.current
    if (!svg) return
    const clone = svg.cloneNode(true) as SVGSVGElement
    clone.setAttribute('width', String(canvasSize.w))
    clone.setAttribute('height', String(canvasSize.h))
    const grid = clone.querySelector('#editor-grid')
    grid?.remove()
    clone.querySelectorAll('[data-sel-handle]').forEach(el => el.remove())

    const xml = new XMLSerializer().serializeToString(clone)
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = canvasSize.w; canvas.height = canvasSize.h
      const ctx = canvas.getContext('2d')!
      ctx.fillStyle = '#0f0f1a'
      ctx.fillRect(0, 0, canvasSize.w, canvasSize.h)
      ctx.drawImage(img, 0, 0)
      canvas.toBlob(blob => {
        if (!blob) return
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url; a.download = 'rhea-graphic.png'; a.click()
        URL.revokeObjectURL(url)
      })
    }
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(xml)))
  }, [canvasSize])

  // ─── Share ────────────────────────────────────────────────────
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const shareGraphic = useCallback(async () => {
    const svg = svgRef.current
    if (!svg) return
    const clone = svg.cloneNode(true) as SVGSVGElement
    clone.setAttribute('width', String(canvasSize.w))
    clone.setAttribute('height', String(canvasSize.h))
    clone.querySelector('#editor-grid')?.remove()
    clone.querySelectorAll('[data-sel-handle]').forEach(el => el.remove())
    const xml = new XMLSerializer().serializeToString(clone)
    try {
      const resp = await fetch(`${API}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: xml, content_type: 'graphic', title: 'Rhea Graphic' }),
      })
      if (resp.ok) {
        const data = await resp.json()
        const url = `${location.origin}/share/${data.token}`
        setShareUrl(url)
        navigator.clipboard.writeText(url)
        setTimeout(() => setShareUrl(null), 3000)
      }
    } catch { /* silent */ }
  }, [canvasSize])

  // ─── Image drop / paste ────────────────────────────────────────
  const handleImageFile = useCallback((file: File) => {
    const reader = new FileReader()
    reader.onload = () => {
      const img = new Image()
      img.onload = () => {
        const scale = Math.min(400 / img.width, 300 / img.height, 1)
        const shape: GShape = {
          id: uid(), kind: 'image',
          x: 100, y: 100, w: img.width * scale, h: img.height * scale,
          fill: 'transparent', stroke: 'transparent', strokeWidth: 0,
          opacity: 1, rotation: 0, imageData: reader.result as string,
        }
        setShapes(prev => [...prev, shape])
        setSelectedId(shape.id)
      }
      img.src = reader.result as string
    }
    reader.readAsDataURL(file)
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file?.type.startsWith('image/')) handleImageFile(file)
  }, [handleImageFile])

  // ─── Tools config ─────────────────────────────────────────────
  const tools: { mode: ToolMode; label: string; key: string }[] = [
    { mode: 'select', label: '↖', key: 'V' },
    { mode: 'rect', label: '□', key: 'R' },
    { mode: 'ellipse', label: '○', key: 'E' },
    { mode: 'line', label: '╱', key: 'L' },
    { mode: 'arrow', label: '→', key: 'A' },
    { mode: 'text', label: 'T', key: 'T' },
    { mode: 'path', label: '✎', key: 'P' },
  ]

  return (
    <div className="h-screen flex flex-col bg-[#0f0f1a] text-white overflow-hidden">
      {/* Header */}
      <div className="border-b border-white/[0.06] px-4 py-2 flex items-center gap-3 shrink-0">
        <Link href="/cc" className="text-white/40 hover:text-white/60 text-xs">← CC</Link>
        <span className="text-sm font-medium text-white/80">Graphics Studio</span>
        <div className="flex-1" />
        <button onClick={() => setShowGrid(!showGrid)}
          className={`px-2 py-1 text-xs rounded ${showGrid ? 'bg-white/10 text-white/70' : 'text-white/30'}`}>
          Grid
        </button>
        <div className="flex items-center gap-1 text-xs text-white/40">
          <button onClick={() => setZoom(z => clamp(z - 0.1, 0.2, 3))} className="px-1 hover:text-white/60">−</button>
          <span className="w-10 text-center">{Math.round(zoom * 100)}%</span>
          <button onClick={() => setZoom(z => clamp(z + 0.1, 0.2, 3))} className="px-1 hover:text-white/60">+</button>
          <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }) }} className="px-1 hover:text-white/60 ml-1">1:1</button>
        </div>
        <button onClick={exportSVG} className="px-3 py-1 bg-white/10 hover:bg-white/15 text-xs rounded">SVG</button>
        <button onClick={exportPNG} className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-xs rounded font-medium">PNG</button>
        <button onClick={shareGraphic}
          className={`px-3 py-1 text-xs rounded font-medium ${shareUrl ? 'bg-green-600 text-white' : 'bg-indigo-600 hover:bg-indigo-500 text-white'}`}>
          {shareUrl ? 'Link copied' : 'Share'}
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Toolbox sidebar */}
        <div className="w-11 shrink-0 border-r border-white/[0.06] flex flex-col items-center py-2 gap-1">
          {tools.map(t => (
            <button key={t.mode}
              onClick={() => setTool(t.mode)}
              title={`${t.label} (${t.key})`}
              className={`w-8 h-8 rounded flex items-center justify-center text-sm
                ${tool === t.mode ? 'bg-cyan-600 text-white' : 'text-white/40 hover:bg-white/10 hover:text-white/60'}`}>
              {t.label}
            </button>
          ))}
          <div className="flex-1" />
          <div className="space-y-1">
            <button onClick={() => {
              const input = document.createElement('input')
              input.type = 'file'; input.accept = 'image/*'
              input.onchange = () => { if (input.files?.[0]) handleImageFile(input.files[0]) }
              input.click()
            }} className="w-8 h-8 rounded text-white/40 hover:bg-white/10 hover:text-white/60 flex items-center justify-center text-xs"
              title="Import image">
              📷
            </button>
          </div>
        </div>

        {/* Canvas area */}
        <div ref={containerRef} className="flex-1 overflow-auto bg-[#0a0a14] relative"
          onDrop={onDrop} onDragOver={e => e.preventDefault()}>
          <svg
            ref={svgRef}
            width={canvasSize.w * zoom}
            height={canvasSize.h * zoom}
            viewBox={`0 0 ${canvasSize.w} ${canvasSize.h}`}
            onMouseDown={onCanvasMouseDown}
            onMouseMove={onCanvasMouseMove}
            onMouseUp={onCanvasMouseUp}
            onMouseLeave={onCanvasMouseUp}
            style={{ cursor: tool === 'select' ? 'default' : 'crosshair' }}
            className="block"
          >
            <defs>
              <filter id="sel-glow">
                <feDropShadow dx={0} dy={0} stdDeviation={3} floodColor="#06b6d4" floodOpacity={0.6} />
              </filter>
              {showGrid && (
                <pattern id="editor-grid" width={20} height={20} patternUnits="userSpaceOnUse">
                  <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth={0.5} />
                </pattern>
              )}
            </defs>

            {/* Background */}
            <rect width={canvasSize.w} height={canvasSize.h} fill="#0f0f1a" />
            {showGrid && <rect width={canvasSize.w} height={canvasSize.h} fill="url(#editor-grid)" />}

            {/* Shapes */}
            {shapes.map(s => (
              <ShapeSVG key={s.id} shape={s} selected={s.id === selectedId}
                onMouseDown={e => onShapeMouseDown(s.id, e)} />
            ))}

            {/* Selection handles */}
            {selected && tool === 'select' && selected.kind !== 'path' && (
              <g data-sel-handle>
                <SelectionHandles shape={selected} onResize={onResize} />
              </g>
            )}
          </svg>
        </div>

        {/* Right panel: Props + Layers + Tribunal */}
        <div className="w-56 shrink-0 border-l border-white/[0.06] p-3 overflow-y-auto space-y-4">
          {selected ? (
            <PropPanel shape={selected} onChange={patch => updateShape(selected.id, patch)} />
          ) : (
            <div className="text-xs text-white/30">Select a shape to edit properties</div>
          )}

          <div className="border-t border-white/[0.06] pt-3">
            <LayersPanel shapes={shapes} selectedId={selectedId}
              onSelect={setSelectedId} onReorder={reorderShape} onDelete={deleteShape} />
          </div>

          <div className="border-t border-white/[0.06] pt-3">
            <TribunalPanel svgRef={svgRef} shapes={shapes} />
          </div>

          <div className="border-t border-white/[0.06] pt-3 text-[10px] text-white/20 space-y-1">
            <div>V=Select R=Rect E=Ellipse</div>
            <div>L=Line A=Arrow T=Text P=Pen</div>
            <div>Del=Delete ⌘D=Duplicate</div>
            <div>Esc=Deselect</div>
          </div>
        </div>
      </div>
    </div>
  )
}
