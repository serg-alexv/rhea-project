'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import Link from 'next/link'
import * as pdfjsLib from 'pdfjs-dist'

// pdf.js worker — use CDN to avoid webpack bundling issues
if (typeof window !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.9.155/pdf.worker.min.mjs`
}

const API = process.env.NEXT_PUBLIC_CC_API ?? 'http://localhost:8400'

// ─── Types ───────────────────────────────────────────────────────────

interface Annotation {
  id: string
  page: number
  text: string
  rects: DOMRect[]
  tool: 'tribunal' | 'aletheia' | 'note' | 'ontology'
  result?: string
  agreement?: number
  proofId?: string
  ontology?: string
  createdAt: number
}

type AnnotationTool = 'tribunal' | 'aletheia' | 'note' | 'ontology'

const TOOLS: { id: AnnotationTool; label: string; color: string; desc: string }[] = [
  { id: 'tribunal', label: 'Tribunal', color: 'cyan', desc: 'Run consensus on selected claim' },
  { id: 'aletheia', label: 'Aletheia', color: 'emerald', desc: 'Store selection as proof artifact' },
  { id: 'note',     label: 'Note',     color: 'amber', desc: 'Add a personal annotation' },
  { id: 'ontology', label: 'Ontology', color: 'violet', desc: 'Tag with knowledge domain' },
]

const ONTOLOGIES = ['general', 'pharmacology', 'biochemistry', 'logic', 'topology', 'systems_biology']

// ─── PDF Renderer ────────────────────────────────────────────────────

function PDFPage({ page, pageNum, scale, activeTool, onAnnotate }: {
  page: pdfjsLib.PDFPageProxy
  pageNum: number
  scale: number
  activeTool: AnnotationTool
  onAnnotate: (text: string, page: number) => void
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const textRef = useRef<HTMLDivElement>(null)
  const [rendered, setRendered] = useState(false)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const viewport = page.getViewport({ scale })
    canvas.width = viewport.width
    canvas.height = viewport.height

    page.render({ canvasContext: ctx, viewport }).promise.then(() => {
      setRendered(true)
    })

    // Render text layer for selection
    if (textRef.current) {
      textRef.current.innerHTML = ''
      page.getTextContent().then(textContent => {
        const textItems = textContent.items as { str: string; transform: number[]; width: number; height: number }[]
        textItems.forEach(item => {
          if (!item.str.trim()) return
          const tx = pdfjsLib.Util.transform(viewport.transform, item.transform)
          const span = document.createElement('span')
          span.textContent = item.str
          span.style.position = 'absolute'
          span.style.left = `${tx[4]}px`
          span.style.top = `${tx[5] - item.height * scale}px`
          span.style.fontSize = `${item.height * scale}px`
          span.style.fontFamily = 'sans-serif'
          span.style.color = 'transparent'
          span.style.whiteSpace = 'pre'
          span.style.cursor = 'text'
          textRef.current?.appendChild(span)
        })
      })
    }
  }, [page, scale])

  const handleMouseUp = () => {
    const sel = window.getSelection()
    const text = sel?.toString().trim()
    if (text && text.length > 3) {
      onAnnotate(text, pageNum)
      sel?.removeAllRanges()
    }
  }

  return (
    <div className="relative mb-2 mx-auto" style={{ width: page.getViewport({ scale }).width }}>
      <div className="absolute top-1 left-1 text-[9px] font-mono text-white/20 z-10 pointer-events-none">
        p.{pageNum}
      </div>
      <canvas ref={canvasRef} className="block rounded shadow-lg shadow-black/30" />
      <div
        ref={textRef}
        onMouseUp={handleMouseUp}
        className="absolute inset-0 select-text"
        style={{ mixBlendMode: 'multiply' }}
      />
    </div>
  )
}

// ─── Annotation Panel ────────────────────────────────────────────────

function AnnotationItem({ ann, onDelete }: { ann: Annotation; onDelete: (id: string) => void }) {
  const tool = TOOLS.find(t => t.id === ann.tool)
  const colorMap: Record<string, string> = {
    cyan: 'border-cyan-500/30 bg-cyan-500/5',
    emerald: 'border-emerald-500/30 bg-emerald-500/5',
    amber: 'border-amber-500/30 bg-amber-500/5',
    violet: 'border-violet-500/30 bg-violet-500/5',
  }
  const textColorMap: Record<string, string> = {
    cyan: 'text-cyan-400',
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    violet: 'text-violet-400',
  }

  return (
    <div className={`rounded-lg border p-2.5 ${colorMap[tool?.color ?? 'cyan']} mb-2`}>
      <div className="flex items-center justify-between mb-1">
        <span className={`text-[9px] font-bold uppercase tracking-widest ${textColorMap[tool?.color ?? 'cyan']}`}>
          {tool?.label} &middot; p.{ann.page}
        </span>
        <button onClick={() => onDelete(ann.id)} className="text-white/20 hover:text-red-400 text-[10px]">&times;</button>
      </div>
      <p className="text-[10px] text-white/60 font-mono leading-relaxed line-clamp-3 mb-1">
        &ldquo;{ann.text}&rdquo;
      </p>
      {ann.agreement !== undefined && (
        <div className="text-[9px] font-mono text-white/40">
          Agreement: <span className={ann.agreement > 70 ? 'text-emerald-400' : ann.agreement > 40 ? 'text-amber-400' : 'text-red-400'}>
            {ann.agreement}%
          </span>
        </div>
      )}
      {ann.proofId && (
        <div className="text-[9px] font-mono text-emerald-400/50">proof: {ann.proofId.slice(0, 12)}...</div>
      )}
      {ann.ontology && (
        <div className="text-[9px] font-mono text-violet-400/50">domain: {ann.ontology}</div>
      )}
      {ann.result && (
        <details className="mt-1">
          <summary className="text-[9px] text-white/30 cursor-pointer">Result</summary>
          <p className="text-[10px] text-white/50 font-mono leading-relaxed mt-1 whitespace-pre-wrap">
            {ann.result}
          </p>
        </details>
      )}
    </div>
  )
}

// ─── Main Page ───────────────────────────────────────────────────────

export default function PapersPage() {
  const [pdfDoc, setPdfDoc] = useState<pdfjsLib.PDFDocumentProxy | null>(null)
  const [pages, setPages] = useState<pdfjsLib.PDFPageProxy[]>([])
  const [scale, setScale] = useState(1.4)
  const [fileName, setFileName] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTool, setActiveTool] = useState<AnnotationTool>('tribunal')
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [processing, setProcessing] = useState(false)
  const [ontologyPick, setOntologyPick] = useState('general')
  const [noteText, setNoteText] = useState('')
  const [pendingSelection, setPendingSelection] = useState<{ text: string; page: number } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const loadPDF = async (file: File) => {
    setLoading(true)
    setFileName(file.name)
    const buffer = await file.arrayBuffer()
    const doc = await pdfjsLib.getDocument({ data: buffer }).promise
    setPdfDoc(doc)

    const loaded: pdfjsLib.PDFPageProxy[] = []
    for (let i = 1; i <= doc.numPages; i++) {
      loaded.push(await doc.getPage(i))
    }
    setPages(loaded)
    setLoading(false)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file?.type === 'application/pdf') loadPDF(file)
  }, [])

  const handleAnnotate = useCallback((text: string, page: number) => {
    setPendingSelection({ text, page })

    if (activeTool === 'note' || activeTool === 'ontology') return // wait for input

    // Auto-execute for tribunal and aletheia
    executeAnnotation(text, page, activeTool)
  }, [activeTool, ontologyPick])

  const executeAnnotation = async (text: string, page: number, tool: AnnotationTool) => {
    const id = crypto.randomUUID()
    const ann: Annotation = {
      id, page, text, rects: [], tool, createdAt: Date.now(),
    }

    if (tool === 'tribunal') {
      setProcessing(true)
      try {
        const res = await fetch(`${API}/tribunal`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-API-Key': 'dev-bypass' },
          body: JSON.stringify({ prompt: `Evaluate this claim from a research paper: "${text}"`, k: 3 }),
        })
        const data = await res.json()
        ann.result = data.consensus_text || data.result || JSON.stringify(data)
        ann.agreement = data.agreement_score ?? data.agreement
      } catch (e) {
        ann.result = 'Error: tribunal unreachable'
      }
      setProcessing(false)
    }

    if (tool === 'aletheia') {
      setProcessing(true)
      try {
        const res = await fetch(`${API}/aletheia/store`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'hypothesis',
            prompt: text,
            ontology: ontologyPick,
            consensus_text: `Extracted from paper: ${fileName} (p.${page})`,
            agreement_score: 0,
            source: fileName,
          }),
        })
        const data = await res.json()
        ann.proofId = data.id || data.proof_id
        ann.result = `Stored as ${data.type || 'hypothesis'} in Aletheia`
      } catch (e) {
        ann.result = 'Error: aletheia unreachable'
      }
      setProcessing(false)
    }

    if (tool === 'ontology') {
      ann.ontology = ontologyPick
      ann.result = `Tagged as ${ontologyPick}`
    }

    if (tool === 'note') {
      ann.result = noteText || '(empty note)'
      setNoteText('')
    }

    setAnnotations(prev => [ann, ...prev])
    setPendingSelection(null)
  }

  const deleteAnnotation = (id: string) => {
    setAnnotations(prev => prev.filter(a => a.id !== id))
  }

  const pageAnnotations = (pageNum: number) => annotations.filter(a => a.page === pageNum)

  return (
    <div className="h-screen flex flex-col bg-[#0a0b0f] text-white overflow-hidden">
      {/* Header */}
      <div className="border-b border-white/[0.06] px-4 py-3 flex items-center gap-3 shrink-0">
        <Link href="/cc" className="text-white/40 hover:text-white/60 text-xs transition-colors">
          &larr; CC
        </Link>
        <div className="h-3 w-px bg-white/10" />
        <h1 className="text-xs font-bold uppercase tracking-widest text-white/80">
          Papers
        </h1>
        {fileName && (
          <span className="text-[10px] font-mono text-white/30 truncate max-w-xs">{fileName}</span>
        )}
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setScale(s => Math.max(0.5, s - 0.2))}
            className="px-2 py-0.5 text-[10px] text-white/40 hover:text-white/60 border border-white/10 rounded"
          >-</button>
          <span className="text-[10px] font-mono text-white/30">{(scale * 100).toFixed(0)}%</span>
          <button
            onClick={() => setScale(s => Math.min(3, s + 0.2))}
            className="px-2 py-0.5 text-[10px] text-white/40 hover:text-white/60 border border-white/10 rounded"
          >+</button>
          <button
            onClick={() => fileRef.current?.click()}
            className="px-3 py-1 bg-cyan-500/20 border border-cyan-500/30 rounded text-[10px] text-cyan-400 font-mono"
          >
            Open PDF
          </button>
          <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={e => {
            const f = e.target.files?.[0]
            if (f) loadPDF(f)
          }} />
        </div>
      </div>

      {/* Tool bar */}
      <div className="border-b border-white/[0.06] px-4 py-2 flex items-center gap-2 shrink-0">
        <span className="text-[9px] font-bold text-white/30 font-mono mr-1">TOOL</span>
        {TOOLS.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTool(t.id)}
            className={`group relative px-3 py-1 rounded text-[10px] font-mono transition-colors ${
              activeTool === t.id
                ? `bg-${t.color}-500/20 text-${t.color}-400 border border-${t.color}-500/30`
                : 'text-white/30 hover:text-white/50'
            }`}
            style={activeTool === t.id ? {
              backgroundColor: `color-mix(in srgb, ${t.color === 'cyan' ? '#06b6d4' : t.color === 'emerald' ? '#10b981' : t.color === 'amber' ? '#f59e0b' : '#8b5cf6'} 15%, transparent)`,
              color: t.color === 'cyan' ? '#22d3ee' : t.color === 'emerald' ? '#34d399' : t.color === 'amber' ? '#fbbf24' : '#a78bfa',
              borderColor: `color-mix(in srgb, ${t.color === 'cyan' ? '#06b6d4' : t.color === 'emerald' ? '#10b981' : t.color === 'amber' ? '#f59e0b' : '#8b5cf6'} 30%, transparent)`,
              borderWidth: '1px',
              borderStyle: 'solid',
            } : {}}
          >
            {t.label}
            <span className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 bg-black/90 border border-white/10 text-white/60 text-[9px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
              {t.desc}
            </span>
          </button>
        ))}

        {activeTool === 'ontology' && (
          <>
            <div className="h-3 w-px bg-white/10" />
            <select
              value={ontologyPick}
              onChange={e => setOntologyPick(e.target.value)}
              className="bg-black/40 border border-white/10 rounded px-2 py-1 text-[10px] text-white/60 font-mono"
            >
              {ONTOLOGIES.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </>
        )}

        {processing && (
          <span className="text-[10px] text-cyan-400/60 font-mono animate-pulse ml-2">
            Processing...
          </span>
        )}

        <span className="ml-auto text-[9px] text-white/20 font-mono">
          Select text in PDF to annotate with active tool
        </span>
      </div>

      {/* Pending note/ontology input */}
      {pendingSelection && (activeTool === 'note' || activeTool === 'ontology') && (
        <div className="border-b border-amber-500/20 bg-amber-500/[0.03] px-4 py-2 flex items-center gap-2 shrink-0">
          <span className="text-[10px] text-white/40 font-mono shrink-0">
            &ldquo;{pendingSelection.text.slice(0, 60)}...&rdquo; p.{pendingSelection.page}
          </span>
          {activeTool === 'note' && (
            <input
              value={noteText}
              onChange={e => setNoteText(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') executeAnnotation(pendingSelection.text, pendingSelection.page, 'note') }}
              placeholder="Your note..."
              className="flex-1 bg-black/40 border border-white/10 rounded px-2 py-1 text-[10px] text-white/80 font-mono"
              autoFocus
            />
          )}
          <button
            onClick={() => executeAnnotation(pendingSelection.text, pendingSelection.page, activeTool)}
            className="px-2 py-1 bg-amber-500/20 border border-amber-500/30 rounded text-[10px] text-amber-400 font-mono"
          >
            Save
          </button>
          <button
            onClick={() => setPendingSelection(null)}
            className="text-white/20 hover:text-white/40 text-[10px]"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* PDF viewer */}
        <div className="flex-1 overflow-y-auto p-4" onDragOver={e => e.preventDefault()} onDrop={handleDrop}>
          {!pdfDoc && !loading && (
            <div
              className="flex items-center justify-center h-full"
              onDragOver={e => e.preventDefault()}
              onDrop={handleDrop}
            >
              <div className="text-center border-2 border-dashed border-white/10 rounded-2xl p-12 max-w-md">
                <div className="text-3xl text-white/10 mb-3">PDF</div>
                <p className="text-xs text-white/30 mb-4">
                  Drop a paper here or click Open PDF
                </p>
                <p className="text-[10px] text-white/20 leading-relaxed">
                  Select text to annotate with Rhea tools:<br/>
                  <span className="text-cyan-400/40">Tribunal</span> — consensus on claims &middot;
                  <span className="text-emerald-400/40"> Aletheia</span> — store as proof &middot;
                  <span className="text-amber-400/40"> Note</span> — personal annotation &middot;
                  <span className="text-violet-400/40"> Ontology</span> — domain tag
                </p>
              </div>
            </div>
          )}

          {loading && (
            <div className="flex items-center justify-center h-full">
              <span className="text-xs text-cyan-400/60 font-mono animate-pulse">Loading PDF...</span>
            </div>
          )}

          {pages.map((page, i) => (
            <PDFPage
              key={i}
              page={page}
              pageNum={i + 1}
              scale={scale}
              activeTool={activeTool}
              onAnnotate={handleAnnotate}
            />
          ))}
        </div>

        {/* Annotations sidebar */}
        <div className="w-72 shrink-0 border-l border-white/[0.06] bg-black/20 overflow-y-auto p-3">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[10px] font-bold uppercase tracking-widest text-white/40">
              Annotations ({annotations.length})
            </h2>
            {annotations.length > 0 && (
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(annotations, null, 2)], { type: 'application/json' })
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `${fileName?.replace('.pdf', '') || 'paper'}-annotations.json`
                  a.click()
                  URL.revokeObjectURL(url)
                }}
                className="text-[9px] text-white/30 hover:text-white/50 font-mono"
              >
                Export
              </button>
            )}
          </div>

          {annotations.length === 0 && (
            <p className="text-[10px] text-white/20 text-center mt-8">
              Select text in the PDF to create annotations
            </p>
          )}

          {annotations.map(ann => (
            <AnnotationItem key={ann.id} ann={ann} onDelete={deleteAnnotation} />
          ))}
        </div>
      </div>
    </div>
  )
}
