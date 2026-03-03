'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_CC_API ?? 'http://localhost:8400'

// ─── Types ────────────────────────────────────────────────────────────

type NodeKind = 'enzyme' | 'metabolite' | 'complex' | 'gene' | 'cofactor' | 'membrane'
type EdgeKind = 'reaction' | 'electron' | 'proton' | 'regulation' | 'gene_product'

interface BioNode {
  id: string
  label: string
  sublabel?: string
  kind: NodeKind
  x: number
  y: number
  w: number
  h: number
  note?: string
}

interface BioEdge {
  id: string
  from: string
  to: string
  label?: string
  kind: EdgeKind
  reversible?: boolean
}

interface Pathway {
  id: string
  name: string
  description: string
  nodes: BioNode[]
  edges: BioEdge[]
}

interface GeneEntry {
  locus: string
  name: string
  start: number
  end: number
  strand: '+' | '-'
  product: string
  note?: string
  color?: string
}

interface Contig {
  id: string
  name: string
  length: number
  genes: GeneEntry[]
}

// ─── Color map ────────────────────────────────────────────────────────

const NODE_COLORS: Record<NodeKind, { bg: string; border: string; text: string }> = {
  enzyme:     { bg: '#1e3a5f', border: '#3b82f6', text: '#93c5fd' },
  metabolite: { bg: '#1a3a2a', border: '#22c55e', text: '#86efac' },
  complex:    { bg: '#2d1f4a', border: '#8b5cf6', text: '#c4b5fd' },
  gene:       { bg: '#3a2010', border: '#f97316', text: '#fdba74' },
  cofactor:   { bg: '#2a2a10', border: '#eab308', text: '#fde047' },
  membrane:   { bg: '#1a2a3a', border: '#06b6d4', text: '#67e8f9' },
}

const EDGE_COLORS: Record<EdgeKind, string> = {
  reaction:     '#3b82f6',
  electron:     '#a78bfa',
  proton:       '#f97316',
  regulation:   '#ef4444',
  gene_product: '#22c55e',
}

const EDGE_DASH: Record<EdgeKind, string> = {
  reaction:     'none',
  electron:     '6 3',
  proton:       '3 3',
  regulation:   '8 4',
  gene_product: 'none',
}

// ─── Built-in Pathways ────────────────────────────────────────────────

const PATHWAYS: Pathway[] = [
  {
    id: 'respiratory_chain',
    name: 'Respiratory Chain — H32-02',
    description: 'Leuconostoc mesenteroides H32-02 electron transport chain (aerobic). NADH → ndh → menaquinone → cydABCD → O₂',
    nodes: [
      { id: 'nadh',   label: 'NADH',         kind: 'metabolite', x: 60,  y: 180, w: 90,  h: 40, note: 'Electron donor (reduced)' },
      { id: 'nad',    label: 'NAD⁺',          kind: 'metabolite', x: 60,  y: 280, w: 90,  h: 40, note: 'Oxidised product' },
      { id: 'ndh',    label: 'ndh',           sublabel: 'NADH dehydrogenase', kind: 'enzyme', x: 220, y: 200, w: 140, h: 56, note: 'Non-proton-pumping type II NADH:quinone oxidoreductase. Single subunit. Lm-H32 encodes ndh.' },
      { id: 'mq',     label: 'Menaquinone',   sublabel: 'MQH₂ ⇌ MQ', kind: 'cofactor', x: 430, y: 180, w: 120, h: 56, note: 'Lipid-soluble electron carrier in membrane. Characteristic of low-GC Gram-positive bacteria.' },
      { id: 'cyd',    label: 'cydABCD',       sublabel: 'bd-type oxidase', kind: 'complex', x: 630, y: 200, w: 140, h: 56, note: 'Cytochrome bd-type quinol oxidase. High O₂ affinity. Encoded by cydA+cydB+cydC+cydD. Pumps no protons.' },
      { id: 'o2',     label: 'O₂',            kind: 'metabolite', x: 840, y: 160, w: 70,  h: 40, note: 'Terminal electron acceptor (aerobic)' },
      { id: 'h2o',    label: 'H₂O',           kind: 'metabolite', x: 840, y: 240, w: 70,  h: 40, note: 'Reduction product' },
      { id: 'mem',    label: 'Membrane',       kind: 'membrane',   x: 60,  y: 340, w: 860, h: 20, note: 'Cytoplasmic membrane — site of ETC components' },
      { id: 'atp',    label: 'ATP',            kind: 'metabolite', x: 430, y: 330, w: 80,  h: 36, note: 'F₀F₁-ATPase product. ΔΨ drives synthesis.' },
      { id: 'atps',   label: 'F₀F₁ ATPase',   sublabel: 'atpABCDEFGHI', kind: 'complex', x: 360, y: 390, w: 160, h: 56, note: 'ATP synthase complex. Uses proton motive force to synthesise ATP from ADP+Pi.' },
    ],
    edges: [
      { id: 'e1', from: 'nadh', to: 'ndh', label: '2e⁻', kind: 'electron' },
      { id: 'e2', from: 'ndh',  to: 'nad', label: 'H⁺', kind: 'proton' },
      { id: 'e3', from: 'ndh',  to: 'mq',  label: 'MQ→MQH₂', kind: 'electron' },
      { id: 'e4', from: 'mq',   to: 'cyd', label: '2e⁻', kind: 'electron' },
      { id: 'e5', from: 'cyd',  to: 'o2',  label: '½O₂', kind: 'reaction' },
      { id: 'e6', from: 'cyd',  to: 'h2o', label: 'H₂O', kind: 'reaction' },
      { id: 'e7', from: 'atps', to: 'atp', label: 'ADP→ATP', kind: 'reaction' },
    ],
  },
  {
    id: 'defense_systems',
    name: 'Defense Systems — H32-02',
    description: 'Phage defense mechanisms identified in L. mesenteroides H32-02 genome audit',
    nodes: [
      { id: 'phage',    label: 'Phage DNA',      kind: 'metabolite', x: 400, y: 60,  w: 100, h: 40, note: 'Foreign DNA/RNA challenge' },
      { id: 'rm',       label: 'R-M System',      sublabel: 'Type I/II', kind: 'complex', x: 160, y: 180, w: 140, h: 56, note: 'Restriction-Modification. Methylates self-DNA, restricts foreign. Identified in H32-02.' },
      { id: 'crispr',   label: 'CRISPR-Cas',      sublabel: 'Type II-A', kind: 'complex', x: 390, y: 180, w: 140, h: 56, note: 'Adaptive immunity. cas9 orthologue present. Spacer array with 4 spacers targeting known Leuconostoc phages.' },
      { id: 'abortive', label: 'Abortive Inf.',   sublabel: 'AbiA-like', kind: 'enzyme', x: 620, y: 180, w: 140, h: 56, note: 'AbiA-like abortive infection system. Altruistic cell death to protect colony.' },
      { id: 'intact',   label: 'Cell survives',   kind: 'metabolite', x: 160, y: 340, w: 120, h: 40, note: 'DNA restricted, cell intact' },
      { id: 'memory',   label: 'Spacer acquired', kind: 'metabolite', x: 390, y: 340, w: 130, h: 40, note: 'New CRISPR spacer integrated' },
      { id: 'death',    label: 'Cell death',      kind: 'metabolite', x: 620, y: 340, w: 100, h: 40, note: 'Prevents phage spread to colony' },
    ],
    edges: [
      { id: 'd1', from: 'phage', to: 'rm',       label: 'restriction', kind: 'reaction' },
      { id: 'd2', from: 'phage', to: 'crispr',   label: 'recognition', kind: 'reaction' },
      { id: 'd3', from: 'phage', to: 'abortive', label: 'triggers',    kind: 'regulation' },
      { id: 'd4', from: 'rm',       to: 'intact',  label: 'success',   kind: 'reaction' },
      { id: 'd5', from: 'crispr',   to: 'memory',  label: 'adaptation',kind: 'gene_product' },
      { id: 'd6', from: 'abortive', to: 'death',   label: 'lysis',     kind: 'regulation' },
    ],
  },
  {
    id: 'glycolysis',
    name: 'Heterofermentative Glycolysis',
    description: 'L. mesenteroides uses the phosphoketolase (PK) pathway rather than EMP for glucose catabolism',
    nodes: [
      { id: 'glc',  label: 'Glucose',        kind: 'metabolite', x: 400, y: 40,  w: 100, h: 40 },
      { id: 'g6p',  label: 'G6P',            sublabel: 'glucose-6-phosphate', kind: 'metabolite', x: 400, y: 130, w: 120, h: 48 },
      { id: 'r5p',  label: 'Ribulose-5P',    kind: 'metabolite', x: 400, y: 230, w: 120, h: 40 },
      { id: 'pk',   label: 'Phosphoketolase',sublabel: 'xfp', kind: 'enzyme', x: 200, y: 310, w: 140, h: 56, note: 'Key enzyme of the PK pathway. Cleaves xylulose-5P into acetyl-P + GAP.' },
      { id: 'gap',  label: 'GAP',            sublabel: 'glyceraldehyde-3P', kind: 'metabolite', x: 160, y: 430, w: 120, h: 48 },
      { id: 'acp',  label: 'Acetyl-P',       kind: 'metabolite', x: 460, y: 430, w: 100, h: 40 },
      { id: 'lac',  label: 'Lactate',        kind: 'metabolite', x: 100, y: 540, w: 90,  h: 40, note: 'Primary fermentation product' },
      { id: 'eth',  label: 'Ethanol',        kind: 'metabolite', x: 460, y: 540, w: 90,  h: 40, note: 'Secondary fermentation product — heterofermentative signature' },
      { id: 'co2',  label: 'CO₂',            kind: 'metabolite', x: 620, y: 310, w: 70,  h: 40, note: 'Released during decarboxylation' },
      { id: 'ldh',  label: 'LDH',            sublabel: 'lactate dehydrogenase', kind: 'enzyme', x: 80, y: 490, w: 130, h: 48 },
      { id: 'adh',  label: 'ADH/ALDH',       sublabel: 'alcohol dehydrogenase', kind: 'enzyme', x: 430, y: 490, w: 140, h: 48 },
    ],
    edges: [
      { id: 'g1', from: 'glc', to: 'g6p', label: 'hexokinase', kind: 'reaction' },
      { id: 'g2', from: 'g6p', to: 'r5p', label: '6-PGDH/6-PGL', kind: 'reaction' },
      { id: 'g3', from: 'r5p', to: 'pk',  label: 'isomerase', kind: 'reaction' },
      { id: 'g4', from: 'r5p', to: 'co2', label: '-CO₂', kind: 'reaction' },
      { id: 'g5', from: 'pk',  to: 'gap', kind: 'reaction' },
      { id: 'g6', from: 'pk',  to: 'acp', kind: 'reaction' },
      { id: 'g7', from: 'gap', to: 'ldh', kind: 'reaction' },
      { id: 'g8', from: 'ldh', to: 'lac', kind: 'reaction' },
      { id: 'g9', from: 'acp', to: 'adh', kind: 'reaction' },
      { id: 'g10', from: 'adh', to: 'eth', kind: 'reaction' },
    ],
  },
  {
    id: 'custom',
    name: 'Custom Pathway',
    description: 'Build your own pathway from scratch',
    nodes: [],
    edges: [],
  },
]

// ─── Built-in Gene Map Contigs ────────────────────────────────────────

const DEMO_CONTIGS: Contig[] = [
  {
    id: 'c1',
    name: 'H32-02 contig_1 (ETC cluster)',
    length: 12000,
    genes: [
      { locus: 'H32_00001', name: 'ndh',   start: 500,  end: 1900,  strand: '+', product: 'NADH dehydrogenase (type II)', color: '#3b82f6' },
      { locus: 'H32_00002', name: 'menA',  start: 2100, end: 3200,  strand: '+', product: 'Menaquinone biosynthesis', color: '#eab308' },
      { locus: 'H32_00003', name: 'menB',  start: 3400, end: 4500,  strand: '+', product: 'Naphthoate synthase', color: '#eab308' },
      { locus: 'H32_00004', name: 'cydA',  start: 5000, end: 6500,  strand: '+', product: 'Cytochrome bd subunit I', color: '#8b5cf6' },
      { locus: 'H32_00005', name: 'cydB',  start: 6600, end: 7800,  strand: '+', product: 'Cytochrome bd subunit II', color: '#8b5cf6' },
      { locus: 'H32_00006', name: 'cydC',  start: 8000, end: 9200,  strand: '-', product: 'Glutathione ABC transporter', color: '#8b5cf6' },
      { locus: 'H32_00007', name: 'cydD',  start: 9300, end: 10800, strand: '-', product: 'Glutathione ABC transporter subunit', color: '#8b5cf6' },
      { locus: 'H32_00008', name: 'atpA',  start: 11000,end: 11900, strand: '+', product: 'ATP synthase alpha subunit', color: '#22c55e' },
    ],
  },
  {
    id: 'c2',
    name: 'H32-02 contig_3 (CRISPR-defense)',
    length: 8500,
    genes: [
      { locus: 'H32_01001', name: 'cas9',  start: 200,  end: 3900,  strand: '+', product: 'CRISPR-associated endonuclease Cas9', color: '#ef4444' },
      { locus: 'H32_01002', name: 'cas1',  start: 4100, end: 5100,  strand: '+', product: 'CRISPR-associated protein Cas1', color: '#ef4444' },
      { locus: 'H32_01003', name: 'cas2',  start: 5200, end: 5750,  strand: '+', product: 'CRISPR-associated protein Cas2', color: '#ef4444' },
      { locus: 'H32_01004', name: 'tracrRNA', start: 5900, end: 6100, strand: '-', product: 'Trans-activating CRISPR RNA', color: '#f97316', note: 'Non-coding RNA' },
      { locus: 'H32_01005', name: 'CRISPR', start: 6200, end: 7800, strand: '+', product: 'CRISPR array (4 spacers)', color: '#ec4899', note: 'Spacers: φLm1, φLm3, unknown×2' },
      { locus: 'H32_01006', name: 'abiA',  start: 8000, end: 8400, strand: '-', product: 'Abortive infection protein AbiA', color: '#06b6d4' },
    ],
  },
]

// ─── SVG Pathway Renderer ─────────────────────────────────────────────

function getNodeCenter(node: BioNode) {
  return { x: node.x + node.w / 2, y: node.y + node.h / 2 }
}

function edgePath(from: BioNode, to: BioNode): string {
  const a = getNodeCenter(from)
  const b = getNodeCenter(to)
  const dx = b.x - a.x
  const dy = b.y - a.y
  const mx = a.x + dx * 0.5
  const my = a.y + dy * 0.5
  // Slight curve
  const cx = mx + (Math.abs(dy) > Math.abs(dx) ? 30 : 0)
  const cy = my + (Math.abs(dx) > Math.abs(dy) ? 20 : 0)
  return `M${a.x},${a.y} Q${cx},${cy} ${b.x},${b.y}`
}

function arrowHead(from: BioNode, to: BioNode): { x: number; y: number; angle: number } {
  const a = getNodeCenter(from)
  const b = getNodeCenter(to)
  const angle = Math.atan2(b.y - a.y, b.x - a.x) * (180 / Math.PI)
  // Offset endpoint to node edge
  const edgeX = b.x - (to.w / 2 + 8) * Math.cos((angle * Math.PI) / 180)
  const edgeY = b.y - (to.h / 2 + 8) * Math.sin((angle * Math.PI) / 180)
  return { x: edgeX, y: edgeY, angle }
}

function BioNodeSVG({
  node, selected, onMouseDown, onClick,
}: {
  node: BioNode
  selected: boolean
  onMouseDown: (e: React.MouseEvent) => void
  onClick: () => void
}) {
  const c = NODE_COLORS[node.kind]
  const isMemb = node.kind === 'membrane'
  return (
    <g onMouseDown={onMouseDown} onClick={onClick} style={{ cursor: 'move' }}>
      {isMemb ? (
        <rect x={node.x} y={node.y} width={node.w} height={node.h}
          fill={c.bg} stroke={c.border} strokeWidth={selected ? 2.5 : 1}
          rx={4} opacity={0.7} />
      ) : node.kind === 'complex' ? (
        // Complex = hexagon-ish (rounded rect with thick border)
        <rect x={node.x} y={node.y} width={node.w} height={node.h}
          fill={c.bg} stroke={c.border} strokeWidth={selected ? 2.5 : 1.5}
          rx={8}
          filter={selected ? 'url(#bio-glow)' : undefined} />
      ) : node.kind === 'metabolite' || node.kind === 'cofactor' ? (
        // Metabolite = ellipse
        <ellipse cx={node.x + node.w / 2} cy={node.y + node.h / 2}
          rx={node.w / 2} ry={node.h / 2}
          fill={c.bg} stroke={c.border} strokeWidth={selected ? 2.5 : 1.5}
          filter={selected ? 'url(#bio-glow)' : undefined} />
      ) : (
        // Enzyme/gene = rect
        <rect x={node.x} y={node.y} width={node.w} height={node.h}
          fill={c.bg} stroke={c.border} strokeWidth={selected ? 2.5 : 1.5}
          rx={4}
          filter={selected ? 'url(#bio-glow)' : undefined} />
      )}
      {!isMemb && (
        <>
          <text x={node.x + node.w / 2} y={node.y + node.h / 2 - (node.sublabel ? 8 : 0)}
            textAnchor="middle" dominantBaseline="middle"
            fill={c.text} fontSize={12} fontFamily="monospace" fontWeight="bold"
            style={{ pointerEvents: 'none' }}>
            {node.label}
          </text>
          {node.sublabel && (
            <text x={node.x + node.w / 2} y={node.y + node.h / 2 + 10}
              textAnchor="middle" dominantBaseline="middle"
              fill={c.text} fontSize={9} fontFamily="monospace" opacity={0.7}
              style={{ pointerEvents: 'none' }}>
              {node.sublabel}
            </text>
          )}
        </>
      )}
      {isMemb && (
        <text x={node.x + 8} y={node.y + 13}
          fill={c.text} fontSize={9} fontFamily="monospace" opacity={0.6}
          style={{ pointerEvents: 'none' }}>
          {node.label}
        </text>
      )}
    </g>
  )
}

function PathwayCanvas({
  pathway, onNodeSelect, selectedNodeId,
}: {
  pathway: Pathway
  onNodeSelect: (id: string | null) => void
  selectedNodeId: string | null
}) {
  const [nodes, setNodes] = useState<BioNode[]>(pathway.nodes)
  const [dragging, setDragging] = useState<{ id: string; ox: number; oy: number } | null>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 20, y: 20 })
  const svgRef = useRef<SVGSVGElement>(null)
  const [panDrag, setPanDrag] = useState<{ sx: number; sy: number; px: number; py: number } | null>(null)

  useEffect(() => {
    setNodes(pathway.nodes.map(n => ({ ...n })))
  }, [pathway.id])

  const svgPt = useCallback((cx: number, cy: number) => {
    const svg = svgRef.current
    if (!svg) return { x: cx, y: cy }
    const r = svg.getBoundingClientRect()
    return { x: (cx - r.left - pan.x) / zoom, y: (cy - r.top - pan.y) / zoom }
  }, [zoom, pan])

  const onNodeMouseDown = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const pt = svgPt(e.clientX, e.clientY)
    const node = nodes.find(n => n.id === id)
    if (!node) return
    setDragging({ id, ox: pt.x - node.x, oy: pt.y - node.y })
  }, [nodes, svgPt])

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragging) {
      const pt = svgPt(e.clientX, e.clientY)
      setNodes(prev => prev.map(n =>
        n.id === dragging.id ? { ...n, x: pt.x - dragging.ox, y: pt.y - dragging.oy } : n
      ))
    }
    if (panDrag) {
      setPan({ x: panDrag.px + (e.clientX - panDrag.sx), y: panDrag.py + (e.clientY - panDrag.sy) })
    }
  }, [dragging, panDrag, svgPt])

  const onMouseUp = useCallback(() => {
    setDragging(null)
    setPanDrag(null)
  }, [])

  const onCanvasMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 1 || e.altKey) {
      setPanDrag({ sx: e.clientX, sy: e.clientY, px: pan.x, py: pan.y })
      e.preventDefault()
    } else {
      onNodeSelect(null)
    }
  }, [pan, onNodeSelect])

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    setZoom(z => Math.max(0.3, Math.min(3, z - e.deltaY * 0.001)))
  }, [])

  // Build node map for edge rendering
  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]))

  return (
    <div className="relative w-full h-full overflow-hidden bg-[#080810]">
      <svg ref={svgRef} className="w-full h-full" data-pathway-svg
        onMouseDown={onCanvasMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onWheel}
        style={{ cursor: panDrag ? 'grabbing' : 'default' }}>
        <defs>
          <filter id="bio-glow">
            <feDropShadow dx={0} dy={0} stdDeviation={4} floodColor="#06b6d4" floodOpacity={0.7} />
          </filter>
          <marker id="arrowhead" markerWidth={8} markerHeight={8} refX={6} refY={3} orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="#3b82f6" />
          </marker>
          {Object.entries(EDGE_COLORS).map(([kind, color]) => (
            <marker key={kind} id={`arrow-${kind}`} markerWidth={8} markerHeight={8} refX={6} refY={3} orient="auto">
              <path d="M0,0 L0,6 L8,3 z" fill={color} />
            </marker>
          ))}
          <pattern id="bio-grid" width={40} height={40} patternUnits="userSpaceOnUse"
            patternTransform={`translate(${pan.x % 40},${pan.y % 40})`}>
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth={0.5} />
          </pattern>
        </defs>

        {/* Grid */}
        <rect width="100%" height="100%" fill="url(#bio-grid)" />

        <g transform={`translate(${pan.x},${pan.y}) scale(${zoom})`}>
          {/* Edges */}
          {pathway.edges.map(edge => {
            const from = nodeMap[edge.from]
            const to = nodeMap[edge.to]
            if (!from || !to) return null
            const color = EDGE_COLORS[edge.kind]
            const dash = EDGE_DASH[edge.kind]
            const d = edgePath(from, to)
            const arrow = arrowHead(from, to)
            const mid = getNodeCenter(from)
            const midB = getNodeCenter(to)
            const lx = (mid.x + midB.x) / 2
            const ly = (mid.y + midB.y) / 2
            return (
              <g key={edge.id}>
                <path d={d} fill="none" stroke={color} strokeWidth={1.5}
                  strokeDasharray={dash}
                  markerEnd={`url(#arrow-${edge.kind})`}
                  opacity={0.8} />
                {edge.label && (
                  <text x={lx} y={ly - 6} textAnchor="middle"
                    fill={color} fontSize={9} fontFamily="monospace" opacity={0.9}>
                    {edge.label}
                  </text>
                )}
                {edge.reversible && (
                  <path d={edgePath(to, from)} fill="none" stroke={color} strokeWidth={1}
                    strokeDasharray="4 4" opacity={0.4} />
                )}
              </g>
            )
          })}

          {/* Nodes */}
          {nodes.map(node => (
            <BioNodeSVG key={node.id} node={node}
              selected={node.id === selectedNodeId}
              onMouseDown={e => onNodeMouseDown(node.id, e)}
              onClick={() => onNodeSelect(node.id)} />
          ))}
        </g>
      </svg>

      {/* Zoom controls */}
      <div className="absolute bottom-3 right-3 flex items-center gap-1 bg-black/50 rounded-lg px-2 py-1 text-xs text-white/40">
        <button onClick={() => setZoom(z => Math.min(3, z + 0.15))}
          className="px-1.5 hover:text-white/70">+</button>
        <span className="w-10 text-center">{Math.round(zoom * 100)}%</span>
        <button onClick={() => setZoom(z => Math.max(0.3, z - 0.15))}
          className="px-1.5 hover:text-white/70">−</button>
        <button onClick={() => { setZoom(1); setPan({ x: 20, y: 20 }) }}
          className="ml-1 px-1.5 hover:text-white/70">1:1</button>
      </div>

      {/* Alt+drag hint */}
      <div className="absolute bottom-3 left-3 text-[10px] text-white/20">
        Alt+drag to pan · scroll to zoom · drag nodes
      </div>
    </div>
  )
}

// ─── Gene Map ─────────────────────────────────────────────────────────

function GeneMap({ contig, onGeneSelect, selectedGene }: {
  contig: Contig
  onGeneSelect: (g: GeneEntry | null) => void
  selectedGene: GeneEntry | null
}) {
  const TRACK_H = 32
  const LABEL_W = 0
  const scale = (bp: number) => (bp / contig.length) * 900

  return (
    <div className="overflow-x-auto">
      <svg width={960} height={120} className="block">
        <defs>
          <marker id="gene-arrow-plus" markerWidth={6} markerHeight={6} refX={5} refY={3} orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill="rgba(255,255,255,0.3)" />
          </marker>
          <marker id="gene-arrow-minus" markerWidth={6} markerHeight={6} refX={1} refY={3} orient="auto-start-reverse">
            <path d="M6,0 L6,6 L0,3 z" fill="rgba(255,255,255,0.3)" />
          </marker>
        </defs>

        {/* Backbone */}
        <rect x={LABEL_W + 20} y={55} width={920} height={3} fill="rgba(255,255,255,0.1)" rx={1} />

        {/* Scale ticks */}
        {Array.from({ length: 11 }, (_, i) => {
          const bp = Math.round((i / 10) * contig.length)
          const x = LABEL_W + 20 + scale(bp)
          return (
            <g key={i}>
              <line x1={x} y1={50} x2={x} y2={62} stroke="rgba(255,255,255,0.15)" strokeWidth={0.5} />
              <text x={x} y={72} textAnchor="middle" fill="rgba(255,255,255,0.2)" fontSize={8} fontFamily="monospace">
                {bp >= 1000 ? `${(bp / 1000).toFixed(1)}k` : bp}
              </text>
            </g>
          )
        })}

        {/* Genes */}
        {contig.genes.map(gene => {
          const x = LABEL_W + 20 + scale(gene.start)
          const w = Math.max(20, scale(gene.end - gene.start))
          const y = gene.strand === '+' ? 22 : 64
          const isSelected = selectedGene?.locus === gene.locus
          const color = gene.color ?? '#3b82f6'

          return (
            <g key={gene.locus} onClick={() => onGeneSelect(isSelected ? null : gene)}
              style={{ cursor: 'pointer' }}>
              {/* Gene arrow shape */}
              <polygon
                points={gene.strand === '+'
                  ? `${x},${y} ${x + w - 8},${y} ${x + w},${y + 12} ${x + w - 8},${y + 24} ${x},${y + 24}`
                  : `${x + 8},${y} ${x + w},${y} ${x + w},${y + 24} ${x + 8},${y + 24} ${x},${y + 12}`}
                fill={color}
                opacity={isSelected ? 1 : 0.75}
                stroke={isSelected ? 'white' : 'rgba(0,0,0,0.4)'}
                strokeWidth={isSelected ? 1.5 : 0.5}
              />
              {/* Gene name */}
              {w > 30 && (
                <text
                  x={x + w / 2} y={y + 14}
                  textAnchor="middle" dominantBaseline="middle"
                  fill="white" fontSize={9} fontFamily="monospace" fontWeight="bold"
                  style={{ pointerEvents: 'none' }}>
                  {gene.name}
                </text>
              )}
            </g>
          )
        })}
      </svg>
    </div>
  )
}

// ─── Node Detail Panel ────────────────────────────────────────────────

function NodeDetail({ node, pathway }: { node: BioNode; pathway: Pathway }) {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const c = NODE_COLORS[node.kind]

  const ask = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/tribunal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: `In context of the ${pathway.name} pathway, regarding "${node.label}" (${node.kind}): ${query}`,
          k: 2, tier: 'cheap',
        }),
      })
      const data = await res.json()
      setResult(data.consensus ?? data.response ?? data.answer ?? '')
    } catch { setResult('Tribunal unreachable') }
    setLoading(false)
  }

  return (
    <div className="space-y-3 text-xs">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded-full" style={{ background: c.border }} />
        <span className="text-white/50 uppercase tracking-wider">{node.kind}</span>
      </div>
      <div>
        <div className="text-white font-medium font-mono">{node.label}</div>
        {node.sublabel && <div className="text-white/40 mt-0.5">{node.sublabel}</div>}
      </div>
      {node.note && (
        <div className="bg-white/5 rounded p-2 text-white/60 leading-relaxed">{node.note}</div>
      )}

      {/* Connected edges */}
      <div>
        <div className="text-white/30 mb-1">Connections</div>
        {pathway.edges
          .filter(e => e.from === node.id || e.to === node.id)
          .map(e => {
            const other = e.from === node.id ? e.to : e.from
            const dir = e.from === node.id ? '→' : '←'
            const otherNode = pathway.nodes.find(n => n.id === other)
            return (
              <div key={e.id} className="flex items-center gap-1 text-[10px] text-white/40 py-0.5">
                <span style={{ color: EDGE_COLORS[e.kind] }}>{dir}</span>
                <span className="font-mono">{otherNode?.label ?? other}</span>
                {e.label && <span className="text-white/20">({e.label})</span>}
                <span className="ml-auto text-white/20">{e.kind}</span>
              </div>
            )
          })
        }
      </div>

      {/* Tribunal query */}
      <div className="border-t border-white/10 pt-2">
        <div className="text-white/30 mb-1">Ask Tribunal</div>
        <div className="flex gap-1">
          <input value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && ask()}
            placeholder="Ask about this node..."
            className="flex-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-white/80 text-[11px]" />
          <button onClick={ask} disabled={loading}
            className="px-2 py-1 bg-cyan-700 hover:bg-cyan-600 rounded text-white disabled:opacity-40 text-[10px]">
            {loading ? '...' : 'Ask'}
          </button>
        </div>
        {result && (
          <div className="mt-1 text-white/50 bg-white/5 rounded p-2 leading-relaxed max-h-32 overflow-y-auto">
            {result.slice(0, 400)}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Gene Detail Panel ────────────────────────────────────────────────

function GeneDetail({ gene, contig }: { gene: GeneEntry; contig: Contig }) {
  const len = gene.end - gene.start
  return (
    <div className="space-y-2 text-xs">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 rounded" style={{ background: gene.color ?? '#3b82f6' }} />
        <span className="text-white/50 font-mono">{gene.locus}</span>
      </div>
      <div className="text-white font-medium font-mono text-sm">{gene.name}</div>
      <div className="text-white/60 leading-relaxed">{gene.product}</div>
      <div className="grid grid-cols-2 gap-2 mt-2">
        <div className="bg-white/5 rounded p-2">
          <div className="text-white/30">Start</div>
          <div className="font-mono text-white/80">{gene.start.toLocaleString()} bp</div>
        </div>
        <div className="bg-white/5 rounded p-2">
          <div className="text-white/30">End</div>
          <div className="font-mono text-white/80">{gene.end.toLocaleString()} bp</div>
        </div>
        <div className="bg-white/5 rounded p-2">
          <div className="text-white/30">Length</div>
          <div className="font-mono text-white/80">{len.toLocaleString()} bp</div>
        </div>
        <div className="bg-white/5 rounded p-2">
          <div className="text-white/30">Strand</div>
          <div className="font-mono text-white/80">{gene.strand === '+' ? '+ (sense)' : '− (antisense)'}</div>
        </div>
      </div>
      {gene.note && (
        <div className="bg-white/5 rounded p-2 text-white/50 leading-relaxed mt-1">{gene.note}</div>
      )}
    </div>
  )
}

// ─── Export helpers ───────────────────────────────────────────────────

function exportPathwaySVG() {
  const svgEl = document.querySelector<SVGSVGElement>('[data-pathway-svg]')
  if (!svgEl) return
  const clone = svgEl.cloneNode(true) as SVGSVGElement
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.setAttribute('width', '1200')
  clone.setAttribute('height', '700')
  const xml = new XMLSerializer().serializeToString(clone)
  const blob = new Blob([xml], { type: 'image/svg+xml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'rhea-pathway.svg'; a.click()
  URL.revokeObjectURL(url)
}

// ═══════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════

type ViewMode = 'pathway' | 'genes'

export default function BioRendererPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('pathway')
  const [selectedPathwayId, setSelectedPathwayId] = useState<string>('respiratory_chain')
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [selectedContigId, setSelectedContigId] = useState<string>('c1')
  const [selectedGene, setSelectedGene] = useState<GeneEntry | null>(null)

  const pathway = PATHWAYS.find(p => p.id === selectedPathwayId) ?? PATHWAYS[0]
  const selectedNode = pathway.nodes.find(n => n.id === selectedNodeId) ?? null
  const contig = DEMO_CONTIGS.find(c => c.id === selectedContigId) ?? DEMO_CONTIGS[0]

  const TABS = [
    { id: 'pathway' as ViewMode, label: 'Pathways' },
    { id: 'genes' as ViewMode, label: 'Gene Map' },
  ]

  return (
    <div className="h-screen flex flex-col bg-[#0a0a12] text-white overflow-hidden">

      {/* Header */}
      <div className="border-b border-white/[0.06] px-4 py-2 flex items-center gap-3 shrink-0">
        <Link href="/cc" className="text-white/30 hover:text-white/60 text-xs">← CC</Link>
        <span className="text-sm font-medium text-white/70 tracking-wider">BioRenderer</span>
        <span className="text-[10px] text-white/20 bg-white/5 px-2 py-0.5 rounded font-mono">H32-02 L.mesenteroides</span>
        <div className="flex-1" />
        {/* View toggle */}
        <div className="flex rounded-lg border border-white/10 overflow-hidden text-xs">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setViewMode(t.id)}
              className={`px-3 py-1.5 transition-colors ${viewMode === t.id
                ? 'bg-cyan-600/30 text-cyan-300'
                : 'text-white/40 hover:text-white/60'}`}>
              {t.label}
            </button>
          ))}
        </div>
        {viewMode === 'pathway' && (
          <button onClick={() => exportPathwaySVG()}
            className="px-3 py-1.5 bg-white/10 hover:bg-white/15 text-xs rounded text-white/60">
            Export SVG
          </button>
        )}
      </div>

      {/* CC Tab bar */}
      <div className="border-b border-white/[0.06] px-4 flex items-center gap-0 shrink-0">
        <Link href="/cc" className="px-4 py-2 text-xs font-medium text-white/40 hover:text-white/60 border-b-2 border-transparent">Monitor</Link>
        <Link href="/cc/automation" className="px-4 py-2 text-xs font-medium text-white/40 hover:text-white/60 border-b-2 border-transparent">Automation</Link>
        <Link href="/cc/decisions" className="px-4 py-2 text-xs font-medium text-white/40 hover:text-white/60 border-b-2 border-transparent">Decisions</Link>
        <Link href="/cc/papers" className="px-4 py-2 text-xs font-medium text-white/40 hover:text-white/60 border-b-2 border-transparent">Papers</Link>
        <Link href="/cc/graphics" className="px-4 py-2 text-xs font-medium text-white/40 hover:text-white/60 border-b-2 border-transparent">Graphics</Link>
        <Link href="/cc/wallet" className="px-4 py-2 text-xs font-medium text-white/40 hover:text-white/60 border-b-2 border-transparent">Wallet</Link>
        <div className="px-4 py-2 text-xs font-medium text-cyan-400 border-b-2 border-cyan-400">Bio</div>
      </div>

      {/* ─── Pathway View ───────────────────────────────────────────────── */}
      {viewMode === 'pathway' && (
        <div className="flex flex-1 overflow-hidden">
          {/* Left: pathway selector */}
          <div className="w-52 shrink-0 border-r border-white/[0.06] p-3 overflow-y-auto space-y-1">
            <div className="text-[10px] text-white/30 uppercase tracking-widest mb-3">Pathways</div>
            {PATHWAYS.map(p => (
              <button key={p.id}
                onClick={() => { setSelectedPathwayId(p.id); setSelectedNodeId(null) }}
                className={`w-full text-left px-2 py-2 rounded text-xs transition-colors ${
                  selectedPathwayId === p.id
                    ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30'
                    : 'text-white/50 hover:bg-white/5 hover:text-white/70'
                }`}>
                <div className="font-medium">{p.name}</div>
                <div className="text-[10px] opacity-60 mt-0.5 leading-tight">{p.description.slice(0, 60)}…</div>
              </button>
            ))}

            {/* Legend */}
            <div className="border-t border-white/[0.06] pt-3 mt-3 space-y-1.5">
              <div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Legend</div>
              {(Object.entries(NODE_COLORS) as [NodeKind, typeof NODE_COLORS[NodeKind]][]).map(([kind, c]) => (
                <div key={kind} className="flex items-center gap-2 text-[10px]">
                  <div className="w-3 h-3 rounded-sm border" style={{ background: c.bg, borderColor: c.border }} />
                  <span className="text-white/40 capitalize">{kind}</span>
                </div>
              ))}
              <div className="border-t border-white/[0.06] pt-2 space-y-1">
                {(Object.entries(EDGE_COLORS) as [EdgeKind, string][]).map(([kind, color]) => (
                  <div key={kind} className="flex items-center gap-2 text-[10px]">
                    <div className="w-6 h-0.5" style={{ background: color,
                      backgroundImage: EDGE_DASH[kind] !== 'none' ? `repeating-linear-gradient(90deg, ${color} 0 4px, transparent 0 7px)` : undefined }} />
                    <span className="text-white/40 capitalize">{kind.replace('_', ' ')}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Center: pathway canvas */}
          <div className="flex-1 overflow-hidden relative">
            {pathway.nodes.length === 0 ? (
              <div className="flex items-center justify-center h-full text-white/20 text-sm">
                Custom pathway — nodes coming soon
              </div>
            ) : (
              <PathwayCanvas
                pathway={pathway}
                onNodeSelect={setSelectedNodeId}
                selectedNodeId={selectedNodeId}
              />
            )}
          </div>

          {/* Right: node detail */}
          <div className="w-56 shrink-0 border-l border-white/[0.06] p-3 overflow-y-auto">
            {selectedNode ? (
              <NodeDetail node={selectedNode} pathway={pathway} />
            ) : (
              <div className="space-y-3">
                <div className="text-[10px] text-white/30 uppercase tracking-widest">Pathway Info</div>
                <div className="text-sm text-white/80 font-medium">{pathway.name}</div>
                <div className="text-xs text-white/50 leading-relaxed">{pathway.description}</div>
                <div className="grid grid-cols-2 gap-2 text-[11px] mt-3">
                  <div className="bg-white/5 rounded p-2">
                    <div className="text-white/30">Nodes</div>
                    <div className="font-mono text-white/80">{pathway.nodes.length}</div>
                  </div>
                  <div className="bg-white/5 rounded p-2">
                    <div className="text-white/30">Edges</div>
                    <div className="font-mono text-white/80">{pathway.edges.length}</div>
                  </div>
                  {Object.entries(NODE_COLORS).map(([kind]) => {
                    const count = pathway.nodes.filter(n => n.kind === kind as NodeKind).length
                    if (!count) return null
                    return (
                      <div key={kind} className="bg-white/5 rounded p-2">
                        <div className="text-white/30 capitalize">{kind}s</div>
                        <div className="font-mono text-white/80">{count}</div>
                      </div>
                    )
                  })}
                </div>
                <div className="text-[10px] text-white/20 mt-4">Click a node to inspect it</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─── Gene Map View ───────────────────────────────────────────────── */}
      {viewMode === 'genes' && (
        <div className="flex flex-1 overflow-hidden">
          {/* Left: contig selector */}
          <div className="w-52 shrink-0 border-r border-white/[0.06] p-3 overflow-y-auto">
            <div className="text-[10px] text-white/30 uppercase tracking-widest mb-3">Contigs</div>
            {DEMO_CONTIGS.map(c => (
              <button key={c.id}
                onClick={() => { setSelectedContigId(c.id); setSelectedGene(null) }}
                className={`w-full text-left px-2 py-2 rounded text-xs transition-colors mb-1 ${
                  selectedContigId === c.id
                    ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30'
                    : 'text-white/50 hover:bg-white/5'
                }`}>
                <div className="font-medium font-mono">{c.name.split(' ')[1] ?? c.name}</div>
                <div className="text-[10px] opacity-60 mt-0.5">{c.genes.length} genes · {(c.length / 1000).toFixed(1)}kb</div>
              </button>
            ))}

            {/* Color key */}
            <div className="border-t border-white/[0.06] pt-3 mt-3 space-y-1.5">
              <div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Color Key</div>
              {[
                { color: '#3b82f6', label: 'ETC genes' },
                { color: '#8b5cf6', label: 'cyd complex' },
                { color: '#eab308', label: 'Menaquinone' },
                { color: '#22c55e', label: 'ATP synthase' },
                { color: '#ef4444', label: 'CRISPR-Cas' },
                { color: '#f97316', label: 'ncRNA' },
                { color: '#ec4899', label: 'CRISPR array' },
                { color: '#06b6d4', label: 'Abortive inf.' },
              ].map(item => (
                <div key={item.color} className="flex items-center gap-2 text-[10px]">
                  <div className="w-3 h-3 rounded-sm" style={{ background: item.color }} />
                  <span className="text-white/40">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Center: gene map */}
          <div className="flex-1 overflow-auto p-6">
            <div className="mb-2">
              <div className="text-xs text-white/60 font-medium">{contig.name}</div>
              <div className="text-[10px] text-white/30 mt-0.5 font-mono">
                {contig.length.toLocaleString()} bp total · {contig.genes.length} annotated genes
              </div>
            </div>

            <div className="bg-[#080810] rounded-lg border border-white/[0.06] p-4 mt-3">
              <GeneMap contig={contig} onGeneSelect={setSelectedGene} selectedGene={selectedGene} />
            </div>

            {/* Gene table */}
            <div className="mt-6">
              <div className="text-[10px] text-white/30 uppercase tracking-widest mb-3">Gene List</div>
              <div className="space-y-1">
                {contig.genes.map(gene => (
                  <div key={gene.locus}
                    onClick={() => setSelectedGene(selectedGene?.locus === gene.locus ? null : gene)}
                    className={`flex items-center gap-3 px-3 py-2 rounded cursor-pointer text-xs transition-colors ${
                      selectedGene?.locus === gene.locus
                        ? 'bg-white/10 border border-white/20'
                        : 'hover:bg-white/5'
                    }`}>
                    <div className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: gene.color ?? '#3b82f6' }} />
                    <span className="font-mono text-white/70 w-24 shrink-0">{gene.name}</span>
                    <span className="font-mono text-white/30 w-28 shrink-0 text-[10px]">
                      {gene.start.toLocaleString()}–{gene.end.toLocaleString()}
                    </span>
                    <span className={`text-[10px] px-1.5 rounded shrink-0 ${gene.strand === '+' ? 'bg-blue-500/15 text-blue-300' : 'bg-amber-500/15 text-amber-300'}`}>
                      {gene.strand}
                    </span>
                    <span className="text-white/40 truncate flex-1">{gene.product}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: gene detail */}
          <div className="w-56 shrink-0 border-l border-white/[0.06] p-3 overflow-y-auto">
            {selectedGene ? (
              <GeneDetail gene={selectedGene} contig={contig} />
            ) : (
              <div className="space-y-2">
                <div className="text-[10px] text-white/30 uppercase tracking-widest">Contig Info</div>
                <div className="text-sm text-white/60 font-mono">{contig.id}</div>
                <div className="grid grid-cols-1 gap-2 text-[11px] mt-2">
                  <div className="bg-white/5 rounded p-2">
                    <div className="text-white/30">Length</div>
                    <div className="font-mono text-white/80">{contig.length.toLocaleString()} bp</div>
                  </div>
                  <div className="bg-white/5 rounded p-2">
                    <div className="text-white/30">Genes</div>
                    <div className="font-mono text-white/80">{contig.genes.length}</div>
                  </div>
                  <div className="bg-white/5 rounded p-2">
                    <div className="text-white/30">+ strand</div>
                    <div className="font-mono text-white/80">{contig.genes.filter(g => g.strand === '+').length}</div>
                  </div>
                  <div className="bg-white/5 rounded p-2">
                    <div className="text-white/30">− strand</div>
                    <div className="font-mono text-white/80">{contig.genes.filter(g => g.strand === '-').length}</div>
                  </div>
                </div>
                <div className="text-[10px] text-white/20 mt-3">Click a gene to inspect it</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
