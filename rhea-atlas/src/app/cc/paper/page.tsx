'use client'

import { useEffect, useRef, useState, useCallback } from 'react'

/* ── global 3Dmol ── */
declare global { interface Window { $3Dmol: any } }

const API = process.env.NEXT_PUBLIC_CC_API ?? 'http://localhost:8400'

/* ── theme ── */
const bg = '#0a0a0f'
const card = '#111118'
const border = '#1e1e2e'
const accent = '#6366f1'
const green = '#22c55e'
const red = '#ef4444'
const amber = '#f59e0b'
const muted = '#64748b'

/* ── presets ── */
const PDB_PRESETS = [
  { id: '1CRN', name: 'Crambin', cat: 'protein' },
  { id: '1BNA', name: 'B-DNA dodecamer', cat: 'nucleic' },
  { id: '4HHB', name: 'Hemoglobin', cat: 'protein' },
  { id: '5WE4', name: 'ATP synthase', cat: 'enzyme' },
  { id: '6LU7', name: 'SARS-CoV-2 Mpro', cat: 'viral' },
  { id: '1GFL', name: 'GFP', cat: 'protein' },
  { id: '1AO6', name: 'Insulin hexamer', cat: 'protein' },
  { id: '3PQR', name: 'p53-DNA', cat: 'complex' },
  { id: '1JFF', name: 'Glutamine synthetase', cat: 'enzyme' },
  { id: '2POR', name: 'OmpF porin', cat: 'membrane' },
  { id: '1ATP', name: 'Adenylate kinase + ATP', cat: 'enzyme' },
  { id: '3NIR', name: 'CRISPR-Cas9', cat: 'nucleic' },
]

const RENDER_STYLES: { key: string; label: string }[] = [
  { key: 'cartoon', label: 'Cartoon' },
  { key: 'stick', label: 'Stick' },
  { key: 'sphere', label: 'Sphere' },
  { key: 'surface', label: 'Surface' },
  { key: 'line', label: 'Line' },
  { key: 'cross', label: 'Cross' },
]

const COLOR_SCHEMES: { key: string; label: string }[] = [
  { key: 'spectrum', label: 'Rainbow' },
  { key: 'chain', label: 'Chain' },
  { key: 'ss', label: 'Sec. Structure' },
  { key: 'residue', label: 'Residue' },
  { key: 'atom', label: 'Element (CPK)' },
  { key: 'bfactor', label: 'B-factor' },
]

const PANEL_LAYOUTS = ['1x1', '1x2', '2x1', '2x2'] as const
type PanelLayout = typeof PANEL_LAYOUTS[number]

const BG_PRESETS = [
  { key: '#0a0a0f', label: 'Dark' },
  { key: '#ffffff', label: 'White' },
  { key: '#000000', label: 'Black' },
  { key: '#1a1a2e', label: 'Navy' },
  { key: 'gradient-dark', label: 'Grad Dark' },
  { key: 'gradient-light', label: 'Grad Light' },
]

/* ── types ── */
interface Annotation {
  id: string
  type: 'label' | 'arrow' | 'scale' | 'measure'
  x: number
  y: number
  text: string
  targetX?: number
  targetY?: number
  color: string
  fontSize: number
  scaleLength?: number   /* pixels for scale bar */
  scaleAngstroms?: number /* real-world angstroms */
  distanceA?: number     /* measured distance in angstroms */
}

interface SavedFigure {
  id: string
  name: string
  timestamp: number
  layout: PanelLayout
  panels: FigurePanel[]
  caption: string
  figureTitle: string
  sections: ArticleSection[]
  thumbnail?: string
}

interface FigurePanel {
  id: string
  pdbId: string
  label: string
  style: string
  colorScheme: string
  annotations: Annotation[]
  bgColor: string
}

interface ArticleSection {
  id: string
  type: 'heading' | 'text' | 'figure-ref'
  content: string
}

/* ── helpers ── */
let _annId = 0
const newId = () => `ann_${Date.now()}_${_annId++}`
const panelId = () => `panel_${Date.now()}_${_annId++}`

function layoutGrid(layout: PanelLayout): { cols: number; rows: number } {
  const [c, r] = layout.split('x').map(Number)
  return { cols: c, rows: r }
}

function panelCount(layout: PanelLayout): number {
  const { cols, rows } = layoutGrid(layout)
  return cols * rows
}

/* ── main component ── */
export default function PaperPage() {
  /* 3Dmol loading */
  const [molReady, setMolReady] = useState(false)
  const viewersRef = useRef<Record<string, any>>({})
  const containerRefs = useRef<Record<string, HTMLDivElement | null>>({})

  /* figure state */
  const [layout, setLayout] = useState<PanelLayout>('1x1')
  const [panels, setPanels] = useState<FigurePanel[]>([
    { id: panelId(), pdbId: '1CRN', label: 'A', style: 'cartoon', colorScheme: 'spectrum', annotations: [], bgColor: '#0a0a0f' },
  ])
  const [activePanel, setActivePanel] = useState<string>('')
  const [caption, setCaption] = useState('')
  const [figureTitle, setFigureTitle] = useState('Figure 1')

  /* annotation tool */
  type Tool = 'none' | 'label' | 'arrow' | 'scale' | 'measure'
  const [tool, setTool] = useState<Tool>('none')
  const [arrowStart, setArrowStart] = useState<{ x: number; y: number } | null>(null)
  const [measureStart, setMeasureStart] = useState<{ x: number; y: number } | null>(null)
  const [labelText, setLabelText] = useState('Label')
  const [annColor, setAnnColor] = useState('#ffffff')
  const [annFontSize, setAnnFontSize] = useState(14)
  const [dragging, setDragging] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })

  /* save/load figures */
  const [savedFigures, setSavedFigures] = useState<SavedFigure[]>([])
  const [showSavedPanel, setShowSavedPanel] = useState(false)

  /* rotation sync */
  const [rotationSync, setRotationSync] = useState(false)

  /* file upload ref */
  const fileInputRef = useRef<HTMLInputElement>(null)

  /* figure numbering (article mode) */
  const [figureCounter, setFigureCounter] = useState(1)
  const [figureRefs, setFigureRefs] = useState<{ num: number; title: string; caption: string }[]>([])

  /* article state */
  const [mode, setMode] = useState<'figure' | 'article'>('figure')
  const [sections, setSections] = useState<ArticleSection[]>([
    { id: 'title', type: 'heading', content: '' },
    { id: 'abstract', type: 'text', content: '' },
    { id: 'body', type: 'text', content: '' },
  ])

  /* PDB loading state */
  const [loading, setLoading] = useState<Record<string, boolean>>({})
  const [pdbInput, setPdbInput] = useState('')

  /* ── load 3Dmol.js ── */
  useEffect(() => {
    if (window.$3Dmol) { setMolReady(true); return }
    const s = document.createElement('script')
    s.src = 'https://3dmol.org/build/3Dmol-min.js'
    s.onload = () => setMolReady(true)
    document.head.appendChild(s)
  }, [])

  /* load saved figures from localStorage */
  useEffect(() => {
    try {
      const raw = localStorage.getItem('rhea_saved_figures')
      if (raw) setSavedFigures(JSON.parse(raw))
    } catch (_e) { /* ignore */ }
  }, [])

  /* set active panel */
  useEffect(() => {
    if (panels.length > 0 && !panels.find(p => p.id === activePanel)) {
      setActivePanel(panels[0].id)
    }
  }, [panels, activePanel])

  /* ── sync panels with layout ── */
  useEffect(() => {
    const count = panelCount(layout)
    setPanels(prev => {
      if (prev.length >= count) return prev.slice(0, count)
      const labels = 'ABCDEFGH'
      const added: FigurePanel[] = []
      for (let i = prev.length; i < count; i++) {
        added.push({
          id: panelId(),
          pdbId: '',
          label: labels[i] || String(i + 1),
          style: 'cartoon',
          colorScheme: 'spectrum',
          annotations: [],
          bgColor: '#0a0a0f',
        })
      }
      return [...prev, ...added]
    })
  }, [layout])

  /* ── initialize / update viewers ── */
  const initViewer = useCallback((panel: FigurePanel) => {
    if (!molReady) return
    const container = containerRefs.current[panel.id]
    if (!container) return

    // Destroy previous viewer
    if (viewersRef.current[panel.id]) {
      try { viewersRef.current[panel.id].clear() } catch (_e) { /* ignore */ }
    }
    container.innerHTML = ''

    const actualBg = panel.bgColor.startsWith('gradient') ? '#000000' : panel.bgColor
    const viewer = window.$3Dmol.createViewer(container, {
      backgroundColor: actualBg,
      antialias: true,
    })
    /* apply gradient via CSS if needed */
    if (panel.bgColor === 'gradient-dark') {
      container.style.background = 'linear-gradient(180deg, #0a0a2e 0%, #0a0a0f 100%)'
    } else if (panel.bgColor === 'gradient-light') {
      container.style.background = 'linear-gradient(180deg, #e8eaf0 0%, #c0c4d0 100%)'
    } else {
      container.style.background = ''
    }
    viewersRef.current[panel.id] = viewer

    if (panel.pdbId) {
      setLoading(prev => ({ ...prev, [panel.id]: true }))
      window.$3Dmol.download(`pdb:${panel.pdbId}`, viewer, {}, () => {
        applyStyle(viewer, panel.style, panel.colorScheme)
        viewer.zoomTo()
        viewer.render()
        setLoading(prev => ({ ...prev, [panel.id]: false }))
      })
    }
  }, [molReady])

  /* re-init viewers when panels change or molReady */
  useEffect(() => {
    if (!molReady) return
    /* small delay to let refs attach */
    const t = setTimeout(() => {
      panels.forEach(p => {
        if (containerRefs.current[p.id] && p.pdbId) {
          initViewer(p)
        }
      })
    }, 100)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [molReady, panels.length])

  function applyStyle(viewer: any, style: string, colorScheme: string) {
    const colorSpec = colorScheme === 'atom' ? {} :
      colorScheme === 'bfactor' ? { prop: 'b', gradient: 'roygb' } :
      colorScheme === 'chain' ? { prop: 'chain', gradient: 'roygb' } :
      colorScheme === 'ss' ? { prop: 'ss', map: { h: 'red', s: 'blue', c: 'gray' } } :
      colorScheme === 'residue' ? { prop: 'resi', gradient: 'roygb' } :
      { gradient: 'roygb' } /* spectrum */

    if (style === 'surface') {
      viewer.setStyle({}, { cartoon: { color: colorSpec } })
      viewer.addSurface(window.$3Dmol.SurfaceType.VDW, { opacity: 0.7, color: 'white' })
    } else {
      const s: Record<string, any> = {}
      s[style] = colorScheme === 'atom' ? {} : { color: colorSpec }
      viewer.setStyle({}, s)
    }
    viewer.render()
  }

  /* ── rotation sync ── */
  useEffect(() => {
    if (!rotationSync || !molReady) return
    const ids = panels.map(p => p.id)
    if (ids.length < 2) return

    let syncing = false
    const interval = setInterval(() => {
      if (syncing) return
      const primary = viewersRef.current[ids[0]]
      if (!primary) return
      try {
        const view = primary.getView()
        if (!view) return
        syncing = true
        for (let i = 1; i < ids.length; i++) {
          const v = viewersRef.current[ids[i]]
          if (v) { v.setView(view); v.render() }
        }
        syncing = false
      } catch (_e) { syncing = false }
    }, 100)
    return () => clearInterval(interval)
  }, [rotationSync, molReady, panels])

  /* ── file upload handler ── */
  function handleFileUpload(file: File) {
    if (!activePanel || !molReady) return
    const ext = file.name.split('.').pop()?.toLowerCase()
    const format = ext === 'cif' ? 'cif' : 'pdb'
    const reader = new FileReader()
    reader.onload = (ev) => {
      const data = ev.target?.result as string
      if (!data) return
      const container = containerRefs.current[activePanel]
      if (!container) return
      /* clear and recreate viewer */
      if (viewersRef.current[activePanel]) {
        try { viewersRef.current[activePanel].clear() } catch (_e) { /* */ }
      }
      container.innerHTML = ''
      const panel = panels.find(p => p.id === activePanel)
      const bgc = panel?.bgColor?.startsWith('gradient') ? '#000000' : (panel?.bgColor || bg)
      const viewer = window.$3Dmol.createViewer(container, { backgroundColor: bgc, antialias: true })
      viewersRef.current[activePanel] = viewer
      viewer.addModel(data, format)
      applyStyle(viewer, panel?.style || 'cartoon', panel?.colorScheme || 'spectrum')
      viewer.zoomTo()
      viewer.render()
      /* update panel label with file name */
      const shortName = file.name.replace(/\.(pdb|cif)$/i, '').substring(0, 12).toUpperCase()
      setPanels(prev => prev.map(p => p.id === activePanel ? { ...p, pdbId: `FILE:${shortName}` } : p))
    }
    reader.readAsText(file)
  }

  function handleFileDrop(e: React.DragEvent, panelIdx: string) {
    e.preventDefault()
    e.stopPropagation()
    setActivePanel(panelIdx)
    const file = e.dataTransfer.files?.[0]
    if (file && /\.(pdb|cif)$/i.test(file.name)) {
      /* small delay to let activePanel update */
      setTimeout(() => handleFileUpload(file), 50)
    }
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    e.stopPropagation()
  }

  /* ── save / load figures ── */
  function saveFigure() {
    /* generate thumbnail from first panel */
    let thumbnail = ''
    try {
      const viewer = viewersRef.current[panels[0]?.id]
      if (viewer) thumbnail = viewer.pngURI()
    } catch (_e) { /* */ }

    const fig: SavedFigure = {
      id: `fig_${Date.now()}`,
      name: figureTitle || `Figure ${savedFigures.length + 1}`,
      timestamp: Date.now(),
      layout,
      panels: panels.map(p => ({ ...p })),
      caption,
      figureTitle,
      sections: sections.map(s => ({ ...s })),
      thumbnail,
    }
    const updated = [...savedFigures, fig]
    setSavedFigures(updated)
    try { localStorage.setItem('rhea_saved_figures', JSON.stringify(updated)) } catch (_e) { /* */ }
  }

  function loadFigure(fig: SavedFigure) {
    setLayout(fig.layout)
    setPanels(fig.panels.map(p => ({ ...p, annotations: [...(p.annotations || [])] })))
    setCaption(fig.caption)
    setFigureTitle(fig.figureTitle)
    setSections(fig.sections.map(s => ({ ...s })))
    setShowSavedPanel(false)
    /* re-init viewers after state updates */
    setTimeout(() => {
      fig.panels.forEach(p => {
        if (p.pdbId && !p.pdbId.startsWith('FILE:')) {
          initViewer(p)
        }
      })
    }, 200)
  }

  function deleteSavedFigure(figId: string) {
    const updated = savedFigures.filter(f => f.id !== figId)
    setSavedFigures(updated)
    try { localStorage.setItem('rhea_saved_figures', JSON.stringify(updated)) } catch (_e) { /* */ }
  }

  /* ── change background color ── */
  function changeBgColor(color: string) {
    setPanels(prev => prev.map(p => p.id === activePanel ? { ...p, bgColor: color } : p))
    const viewer = viewersRef.current[activePanel]
    if (viewer) {
      const actualBg = color.startsWith('gradient') ? '#000000' : color
      viewer.setBackgroundColor(actualBg)
      viewer.render()
    }
    /* apply gradient via CSS */
    const container = containerRefs.current[activePanel]
    if (container) {
      if (color === 'gradient-dark') {
        container.style.background = 'linear-gradient(180deg, #0a0a2e 0%, #0a0a0f 100%)'
      } else if (color === 'gradient-light') {
        container.style.background = 'linear-gradient(180deg, #e8eaf0 0%, #c0c4d0 100%)'
      } else {
        container.style.background = ''
      }
    }
  }

  /* ── estimate angstroms per pixel from viewer zoom ── */
  function estimateScale(panelIdx: string): number {
    const viewer = viewersRef.current[panelIdx]
    if (!viewer) return 1
    try {
      const slab = viewer.getView()
      /* slab[4] is the zoom distance; approximate: angstroms/pixel ~ zoomDist / containerWidth */
      const container = containerRefs.current[panelIdx]
      const w = container?.clientWidth || 400
      const zoomDist = slab?.[4] || 50
      return zoomDist / (w * 0.5)
    } catch (_e) { return 0.1 }
  }

  /* ── add scale bar annotation ── */
  function addScaleBar(panelIdx: string) {
    const scale = estimateScale(panelIdx) /* angstroms per pixel */
    const targetAngstroms = 10
    const pixelLength = targetAngstroms / scale
    const container = containerRefs.current[panelIdx]
    const w = container?.clientWidth || 400
    const h = container?.clientHeight || 300
    const ann: Annotation = {
      id: newId(),
      type: 'scale',
      x: w - pixelLength - 30,
      y: h - 30,
      text: `${targetAngstroms} A`,
      targetX: w - 30,
      targetY: h - 30,
      color: annColor,
      fontSize: annFontSize,
      scaleLength: pixelLength,
      scaleAngstroms: targetAngstroms,
    }
    setPanels(prev => prev.map(p =>
      p.id === panelIdx ? { ...p, annotations: [...p.annotations, ann] } : p
    ))
  }

  /* ── add figure to reference list (article mode) ── */
  function addFigureRef() {
    const num = figureCounter
    setFigureRefs(prev => [...prev, { num, title: figureTitle, caption }])
    setFigureTitle(`Figure ${num + 1}`)
    setFigureCounter(num + 1)
  }

  /* ── load PDB into active panel ── */
  function loadPDB(pdbId: string) {
    if (!pdbId || !activePanel) return
    setPanels(prev => prev.map(p => p.id === activePanel ? { ...p, pdbId: pdbId.toUpperCase() } : p))
    const panel = panels.find(p => p.id === activePanel)
    if (!panel) return
    const updated = { ...panel, pdbId: pdbId.toUpperCase() }
    setTimeout(() => initViewer(updated), 50)
  }

  /* ── change style on active panel ── */
  function changeStyle(style: string) {
    setPanels(prev => prev.map(p => p.id === activePanel ? { ...p, style } : p))
    const viewer = viewersRef.current[activePanel]
    const panel = panels.find(p => p.id === activePanel)
    if (viewer && panel) {
      viewer.removeAllSurfaces()
      applyStyle(viewer, style, panel.colorScheme)
    }
  }

  function changeColor(colorScheme: string) {
    setPanels(prev => prev.map(p => p.id === activePanel ? { ...p, colorScheme } : p))
    const viewer = viewersRef.current[activePanel]
    const panel = panels.find(p => p.id === activePanel)
    if (viewer && panel) {
      viewer.removeAllSurfaces()
      applyStyle(viewer, panel.style, colorScheme)
    }
  }

  /* ── annotation handlers ── */
  function handleSvgClick(e: React.MouseEvent<SVGSVGElement>, panelIdx: string) {
    if (tool === 'none') return
    const svg = e.currentTarget
    const rect = svg.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    if (tool === 'label') {
      const ann: Annotation = {
        id: newId(), type: 'label', x, y,
        text: labelText, color: annColor, fontSize: annFontSize,
      }
      setPanels(prev => prev.map(p =>
        p.id === panelIdx ? { ...p, annotations: [...p.annotations, ann] } : p
      ))
      setTool('none')
    } else if (tool === 'arrow') {
      if (!arrowStart) {
        setArrowStart({ x, y })
      } else {
        const ann: Annotation = {
          id: newId(), type: 'arrow',
          x: arrowStart.x, y: arrowStart.y,
          targetX: x, targetY: y,
          text: labelText, color: annColor, fontSize: annFontSize,
        }
        setPanels(prev => prev.map(p =>
          p.id === panelIdx ? { ...p, annotations: [...p.annotations, ann] } : p
        ))
        setArrowStart(null)
        setTool('none')
      }
    } else if (tool === 'scale') {
      addScaleBar(panelIdx)
      setTool('none')
    } else if (tool === 'measure') {
      if (!measureStart) {
        setMeasureStart({ x, y })
      } else {
        /* compute distance in angstroms using pixel distance and scale */
        const dx = x - measureStart.x
        const dy = y - measureStart.y
        const pixelDist = Math.sqrt(dx * dx + dy * dy)
        const scale = estimateScale(panelIdx)
        const distA = pixelDist * scale
        const ann: Annotation = {
          id: newId(), type: 'measure',
          x: measureStart.x, y: measureStart.y,
          targetX: x, targetY: y,
          text: `${distA.toFixed(1)} A`,
          color: annColor, fontSize: annFontSize,
          distanceA: distA,
        }
        setPanels(prev => prev.map(p =>
          p.id === panelIdx ? { ...p, annotations: [...p.annotations, ann] } : p
        ))
        setMeasureStart(null)
        setTool('none')
      }
    }
  }

  function handleAnnMouseDown(e: React.MouseEvent, annId: string, panelIdx: string) {
    e.stopPropagation()
    const svg = (e.currentTarget as SVGElement).closest('svg')
    if (!svg) return
    const rect = svg.getBoundingClientRect()
    const panel = panels.find(p => p.id === panelIdx)
    const ann = panel?.annotations.find(a => a.id === annId)
    if (!ann) return
    setDragging(annId)
    setDragOffset({ x: e.clientX - rect.left - ann.x, y: e.clientY - rect.top - ann.y })
  }

  function handleSvgMouseMove(e: React.MouseEvent<SVGSVGElement>, panelIdx: string) {
    if (!dragging) return
    const rect = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - rect.left - dragOffset.x
    const y = e.clientY - rect.top - dragOffset.y
    setPanels(prev => prev.map(p =>
      p.id === panelIdx
        ? { ...p, annotations: p.annotations.map(a => a.id === dragging ? { ...a, x, y } : a) }
        : p
    ))
  }

  function handleSvgMouseUp() { setDragging(null) }

  function deleteAnnotation(annId: string, panelIdx: string) {
    setPanels(prev => prev.map(p =>
      p.id === panelIdx ? { ...p, annotations: p.annotations.filter(a => a.id !== annId) } : p
    ))
  }

  function clearAnnotations() {
    setPanels(prev => prev.map(p =>
      p.id === activePanel ? { ...p, annotations: [] } : p
    ))
  }

  /* ── export figure ── */
  async function exportFigure() {
    const figDiv = document.getElementById('figure-export-area')
    if (!figDiv) return

    try {
      /* Use html2canvas approach: capture each viewer as PNG, compose with annotations */
      const canvases: { panelId: string; dataUrl: string }[] = []
      for (const panel of panels) {
        const viewer = viewersRef.current[panel.id]
        if (viewer) {
          const uri = viewer.pngURI()
          canvases.push({ panelId: panel.id, dataUrl: uri })
        }
      }

      /* Create composite canvas */
      const { cols, rows } = layoutGrid(layout)
      const panelW = 600
      const panelH = 450
      const pad = 8
      const captionH = caption ? 60 : 0
      const titleH = figureTitle ? 32 : 0
      const totalW = cols * panelW + (cols + 1) * pad
      const totalH = titleH + rows * panelH + (rows + 1) * pad + captionH

      const canvas = document.createElement('canvas')
      canvas.width = totalW * 2  /* 2x for retina */
      canvas.height = totalH * 2
      const ctx = canvas.getContext('2d')!
      ctx.scale(2, 2)
      ctx.fillStyle = bg
      ctx.fillRect(0, 0, totalW, totalH)

      /* Title */
      if (figureTitle) {
        ctx.fillStyle = '#e2e8f0'
        ctx.font = 'bold 18px system-ui, -apple-system, sans-serif'
        ctx.fillText(figureTitle, pad, 22)
      }

      /* Draw panels */
      for (let i = 0; i < panels.length; i++) {
        const panel = panels[i]
        const col = i % cols
        const row = Math.floor(i / cols)
        const x = pad + col * (panelW + pad)
        const y = titleH + pad + row * (panelH + pad)

        /* Draw viewer image */
        const canvasData = canvases.find(c => c.panelId === panel.id)
        if (canvasData) {
          const img = new Image()
          await new Promise<void>((resolve) => {
            img.onload = () => {
              ctx.drawImage(img, x, y, panelW, panelH)
              resolve()
            }
            img.src = canvasData.dataUrl
          })
        }

        /* Draw panel label */
        if (panels.length > 1) {
          ctx.fillStyle = 'rgba(0,0,0,0.6)'
          ctx.fillRect(x + 4, y + 4, 24, 22)
          ctx.fillStyle = '#ffffff'
          ctx.font = 'bold 16px system-ui'
          ctx.fillText(panel.label, x + 8, y + 21)
        }

        /* Draw annotations */
        for (const ann of panel.annotations) {
          const ax = x + ann.x
          const ay = y + ann.y
          if (ann.type === 'label') {
            ctx.font = `bold ${ann.fontSize}px system-ui`
            const metrics = ctx.measureText(ann.text)
            const tw = metrics.width + 8
            const th = ann.fontSize + 6
            ctx.fillStyle = 'rgba(0,0,0,0.7)'
            ctx.beginPath()
            ctx.roundRect(ax - 2, ay - ann.fontSize, tw, th, 3)
            ctx.fill()
            ctx.fillStyle = ann.color
            ctx.fillText(ann.text, ax + 2, ay - 2)
          } else if (ann.type === 'arrow' && ann.targetX !== undefined && ann.targetY !== undefined) {
            const tx = x + ann.targetX
            const ty = y + ann.targetY
            ctx.strokeStyle = ann.color
            ctx.lineWidth = 2
            ctx.beginPath()
            ctx.moveTo(ax, ay)
            ctx.lineTo(tx, ty)
            ctx.stroke()
            /* Arrowhead */
            const angle = Math.atan2(ty - ay, tx - ax)
            ctx.beginPath()
            ctx.moveTo(tx, ty)
            ctx.lineTo(tx - 10 * Math.cos(angle - 0.4), ty - 10 * Math.sin(angle - 0.4))
            ctx.lineTo(tx - 10 * Math.cos(angle + 0.4), ty - 10 * Math.sin(angle + 0.4))
            ctx.closePath()
            ctx.fillStyle = ann.color
            ctx.fill()
            /* Label text near start */
            if (ann.text) {
              ctx.font = `bold ${ann.fontSize}px system-ui`
              ctx.fillStyle = ann.color
              ctx.fillText(ann.text, ax + 4, ay - 6)
            }
          } else if (ann.type === 'scale' && ann.targetX !== undefined && ann.targetY !== undefined) {
            const tx = x + ann.targetX
            const ty = y + ann.targetY
            /* Main bar */
            ctx.strokeStyle = ann.color
            ctx.lineWidth = 3
            ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(tx, ty); ctx.stroke()
            /* End ticks */
            ctx.lineWidth = 2
            ctx.beginPath(); ctx.moveTo(ax, ay - 5); ctx.lineTo(ax, ay + 5); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(tx, ty - 5); ctx.lineTo(tx, ty + 5); ctx.stroke()
            /* Label */
            if (ann.text) {
              ctx.font = `bold ${ann.fontSize}px system-ui`
              ctx.textAlign = 'center'
              const midX = (ax + tx) / 2
              ctx.fillStyle = 'rgba(0,0,0,0.7)'
              const tw = ctx.measureText(ann.text).width + 8
              ctx.fillRect(midX - tw / 2, ay - ann.fontSize - 6, tw, ann.fontSize + 4)
              ctx.fillStyle = ann.color
              ctx.fillText(ann.text, midX, ay - ann.fontSize / 2)
              ctx.textAlign = 'left'
            }
          } else if (ann.type === 'measure' && ann.targetX !== undefined && ann.targetY !== undefined) {
            const tx = x + ann.targetX
            const ty = y + ann.targetY
            /* Dashed line */
            ctx.strokeStyle = ann.color
            ctx.lineWidth = 1.5
            ctx.setLineDash([4, 3])
            ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(tx, ty); ctx.stroke()
            ctx.setLineDash([])
            /* Endpoint dots */
            ctx.fillStyle = ann.color
            ctx.beginPath(); ctx.arc(ax, ay, 3, 0, Math.PI * 2); ctx.fill()
            ctx.beginPath(); ctx.arc(tx, ty, 3, 0, Math.PI * 2); ctx.fill()
            /* Distance label at midpoint */
            if (ann.text) {
              ctx.font = `bold ${ann.fontSize}px system-ui`
              ctx.textAlign = 'center'
              const midX = (ax + tx) / 2
              const midY = (ay + ty) / 2
              const tw = ctx.measureText(ann.text).width + 8
              ctx.fillStyle = 'rgba(0,0,0,0.8)'
              ctx.fillRect(midX - tw / 2, midY - ann.fontSize, tw, ann.fontSize + 4)
              ctx.fillStyle = ann.color
              ctx.fillText(ann.text, midX, midY - ann.fontSize / 2 + 5)
              ctx.textAlign = 'left'
            }
          }
        }
      }

      /* Caption */
      if (caption) {
        ctx.fillStyle = '#94a3b8'
        ctx.font = '13px system-ui, -apple-system, sans-serif'
        const cy = titleH + rows * (panelH + pad) + pad + 16
        /* Word wrap caption */
        const words = caption.split(' ')
        let line = ''
        let lineY = cy
        for (const word of words) {
          const test = line + word + ' '
          if (ctx.measureText(test).width > totalW - 2 * pad) {
            ctx.fillText(line.trim(), pad, lineY)
            line = word + ' '
            lineY += 18
          } else {
            line = test
          }
        }
        if (line.trim()) ctx.fillText(line.trim(), pad, lineY)
      }

      /* Download */
      const link = document.createElement('a')
      link.download = `${figureTitle.replace(/\s+/g, '_') || 'figure'}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  /* ── share figure ── */
  async function shareFigure() {
    try {
      /* Generate PNG data URL from first panel */
      const viewer = viewersRef.current[panels[0]?.id]
      if (!viewer) return
      const uri = viewer.pngURI()
      const res = await fetch(`${API}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content_type: 'graphic',
          title: figureTitle || 'Molecular Figure',
          content: `<img src="${uri}" style="max-width:100%;border-radius:8px" />`,
          ttl_hours: 168,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        const url = `${window.location.origin}/share/${data.token}`
        await navigator.clipboard.writeText(url)
        alert('Share link copied!')
      }
    } catch (_e) { /* */ }
  }

  /* ── AI analysis ── */
  const [aiResult, setAiResult] = useState('')
  const [aiLoading, setAiLoading] = useState(false)

  async function askAI() {
    const panel = panels.find(p => p.id === activePanel)
    if (!panel?.pdbId) return
    setAiLoading(true)
    try {
      const res = await fetch(`${API}/keyboard/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: `Describe the structure and biological function of PDB ${panel.pdbId}. Include key structural features, binding sites, and clinical relevance. Be concise but scientifically precise.` }),
      })
      if (res.ok) {
        const data = await res.json()
        setAiResult(data.response || data.text || JSON.stringify(data))
      }
    } catch (_e) { setAiResult('Analysis unavailable') }
    setAiLoading(false)
  }

  /* ── PDB metadata ── */
  const [pdbMeta, setPdbMeta] = useState<Record<string, any> | null>(null)

  async function fetchMeta(pdbId: string) {
    try {
      const res = await fetch(`${API}/bio/lookup?q=${pdbId}`)
      if (res.ok) {
        const data = await res.json()
        setPdbMeta(data.metadata || data)
      }
    } catch (_e) { /* */ }
  }

  /* ── active panel helper ── */
  const ap = panels.find(p => p.id === activePanel)

  /* ═══════════ RENDER ═══════════ */
  return (
    <div style={{ minHeight: '100vh', background: bg, color: '#e2e8f0', fontFamily: 'system-ui, -apple-system, sans-serif' }}>

      {/* ── TOP BAR ── */}
      <header style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px', borderBottom: `1px solid ${border}`, flexWrap: 'wrap' }}>
        <a href="/cc" style={{ color: accent, textDecoration: 'none', fontFamily: 'monospace', fontWeight: 700, fontSize: 14 }}>rhea</a>
        <span style={{ color: muted }}>/</span>
        <span style={{ color: muted, fontSize: 13, fontFamily: 'monospace' }}>paper</span>
        <div style={{ flex: 1 }} />

        {/* Mode toggle */}
        <div style={{ display: 'flex', gap: 2, background: card, borderRadius: 6, padding: 2 }}>
          {(['figure', 'article'] as const).map(m => (
            <button key={m} onClick={() => setMode(m)} style={{
              padding: '5px 14px', borderRadius: 4, border: 'none', cursor: 'pointer',
              background: mode === m ? accent : 'transparent',
              color: mode === m ? '#fff' : muted,
              fontSize: 12, fontFamily: 'monospace', fontWeight: 600,
            }}>
              {m === 'figure' ? 'Figure' : 'Article'}
            </button>
          ))}
        </div>

        {/* Save / Load */}
        <button onClick={saveFigure} style={{
          padding: '5px 12px', borderRadius: 6, border: `1px solid ${amber}44`,
          background: `${amber}11`, color: amber, cursor: 'pointer',
          fontSize: 12, fontFamily: 'monospace', fontWeight: 600,
        }}>
          Save
        </button>
        <button onClick={() => setShowSavedPanel(!showSavedPanel)} style={{
          padding: '5px 12px', borderRadius: 6, border: `1px solid ${muted}44`,
          background: `${muted}11`, color: muted, cursor: 'pointer',
          fontSize: 12, fontFamily: 'monospace', fontWeight: 600, position: 'relative' as const,
        }}>
          Load{savedFigures.length > 0 ? ` (${savedFigures.length})` : ''}
        </button>

        {/* Export */}
        <button onClick={exportFigure} style={{
          padding: '5px 12px', borderRadius: 6, border: `1px solid ${green}44`,
          background: `${green}11`, color: green, cursor: 'pointer',
          fontSize: 12, fontFamily: 'monospace', fontWeight: 600,
        }}>
          Export PNG
        </button>
        <button onClick={shareFigure} style={{
          padding: '5px 12px', borderRadius: 6, border: `1px solid ${accent}44`,
          background: `${accent}11`, color: accent, cursor: 'pointer',
          fontSize: 12, fontFamily: 'monospace', fontWeight: 600,
        }}>
          Share
        </button>
      </header>

      {/* ── SAVED FIGURES PANEL ── */}
      {showSavedPanel && (
        <div style={{
          position: 'absolute', top: 50, right: 16, zIndex: 100,
          width: 320, maxHeight: 400, overflowY: 'auto',
          background: card, border: `1px solid ${border}`, borderRadius: 8,
          boxShadow: '0 8px 32px rgba(0,0,0,0.5)', padding: 12,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 12, fontWeight: 700, fontFamily: 'monospace', color: '#e2e8f0' }}>Saved Figures</span>
            <button onClick={() => setShowSavedPanel(false)} style={{
              background: 'none', border: 'none', color: muted, cursor: 'pointer', fontSize: 16,
            }}>x</button>
          </div>
          {savedFigures.length === 0 ? (
            <div style={{ color: muted, fontSize: 11, fontFamily: 'monospace', textAlign: 'center' as const, padding: 16 }}>
              No saved figures yet
            </div>
          ) : (
            savedFigures.map(fig => (
              <div key={fig.id} style={{
                display: 'flex', gap: 8, alignItems: 'center', padding: 8,
                borderBottom: `1px solid ${border}`, marginBottom: 4,
              }}>
                {fig.thumbnail && (
                  <img src={fig.thumbnail} alt="" style={{ width: 48, height: 36, borderRadius: 4, objectFit: 'cover' as const }} />
                )}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: '#e2e8f0', fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const }}>
                    {fig.name}
                  </div>
                  <div style={{ fontSize: 9, color: muted, fontFamily: 'monospace' }}>
                    {new Date(fig.timestamp).toLocaleDateString()} {fig.layout} {fig.panels.length}p
                  </div>
                </div>
                <button onClick={() => loadFigure(fig)} style={{
                  padding: '3px 8px', background: `${accent}22`, border: `1px solid ${accent}44`,
                  borderRadius: 4, color: accent, cursor: 'pointer', fontSize: 10, fontFamily: 'monospace',
                }}>Load</button>
                <button onClick={() => deleteSavedFigure(fig.id)} style={{
                  padding: '3px 6px', background: 'none', border: `1px solid ${red}44`,
                  borderRadius: 4, color: red, cursor: 'pointer', fontSize: 10, fontFamily: 'monospace',
                }}>x</button>
              </div>
            ))
          )}
        </div>
      )}

      {mode === 'figure' ? (
        <div style={{ display: 'flex', height: 'calc(100vh - 50px)' }}>

          {/* ── LEFT SIDEBAR: PDB + Settings ── */}
          <div style={{ width: 260, borderRight: `1px solid ${border}`, padding: 12, overflowY: 'auto', flexShrink: 0 }}>

            {/* PDB input */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 10, fontWeight: 700, fontFamily: 'monospace', color: muted, display: 'block', marginBottom: 4 }}>PDB ID</label>
              <div style={{ display: 'flex', gap: 4 }}>
                <input
                  value={pdbInput}
                  onChange={e => setPdbInput(e.target.value.toUpperCase())}
                  onKeyDown={e => { if (e.key === 'Enter') { loadPDB(pdbInput); fetchMeta(pdbInput) } }}
                  placeholder="e.g. 1CRN"
                  style={{
                    flex: 1, padding: '6px 8px', background: card, border: `1px solid ${border}`,
                    borderRadius: 6, color: '#e2e8f0', fontSize: 13, fontFamily: 'monospace',
                    outline: 'none',
                  }}
                />
                <button onClick={() => { loadPDB(pdbInput); fetchMeta(pdbInput) }} style={{
                  padding: '6px 10px', background: accent, border: 'none', borderRadius: 6,
                  color: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                }}>Load</button>
              </div>
              {/* File upload */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdb,.cif"
                style={{ display: 'none' }}
                onChange={e => { const f = e.target.files?.[0]; if (f) handleFileUpload(f); e.target.value = '' }}
              />
              <button onClick={() => fileInputRef.current?.click()} style={{
                width: '100%', marginTop: 6, padding: '5px 8px', background: card,
                border: `1px dashed ${border}`, borderRadius: 6, color: muted,
                cursor: 'pointer', fontSize: 11, fontFamily: 'monospace',
              }}>
                Upload .pdb / .cif file
              </button>
            </div>

            {/* Presets */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 10, fontWeight: 700, fontFamily: 'monospace', color: muted, display: 'block', marginBottom: 6 }}>PRESETS</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {PDB_PRESETS.map(p => (
                  <button key={p.id} onClick={() => { setPdbInput(p.id); loadPDB(p.id); fetchMeta(p.id) }} style={{
                    padding: '3px 8px', background: ap?.pdbId === p.id ? `${accent}33` : card,
                    border: `1px solid ${ap?.pdbId === p.id ? accent : border}`,
                    borderRadius: 4, color: ap?.pdbId === p.id ? accent : '#e2e8f0',
                    cursor: 'pointer', fontSize: 10, fontFamily: 'monospace',
                  }}>
                    {p.id}
                  </button>
                ))}
              </div>
            </div>

            {/* Render style */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 10, fontWeight: 700, fontFamily: 'monospace', color: muted, display: 'block', marginBottom: 6 }}>RENDER STYLE</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {RENDER_STYLES.map(s => (
                  <button key={s.key} onClick={() => changeStyle(s.key)} style={{
                    padding: '3px 8px', background: ap?.style === s.key ? `${green}22` : card,
                    border: `1px solid ${ap?.style === s.key ? green : border}`,
                    borderRadius: 4, color: ap?.style === s.key ? green : muted,
                    cursor: 'pointer', fontSize: 10, fontFamily: 'monospace',
                  }}>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Color scheme */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 10, fontWeight: 700, fontFamily: 'monospace', color: muted, display: 'block', marginBottom: 6 }}>COLOR SCHEME</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {COLOR_SCHEMES.map(c => (
                  <button key={c.key} onClick={() => changeColor(c.key)} style={{
                    padding: '3px 8px', background: ap?.colorScheme === c.key ? `${amber}22` : card,
                    border: `1px solid ${ap?.colorScheme === c.key ? amber : border}`,
                    borderRadius: 4, color: ap?.colorScheme === c.key ? amber : muted,
                    cursor: 'pointer', fontSize: 10, fontFamily: 'monospace',
                  }}>
                    {c.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Background color */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 10, fontWeight: 700, fontFamily: 'monospace', color: muted, display: 'block', marginBottom: 6 }}>BACKGROUND</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {BG_PRESETS.map(b => (
                  <button key={b.key} onClick={() => changeBgColor(b.key)} style={{
                    padding: '3px 8px',
                    background: b.key.startsWith('gradient') ? 'linear-gradient(90deg, #333, #666)' : b.key,
                    border: `1px solid ${ap?.bgColor === b.key ? accent : border}`,
                    borderRadius: 4,
                    color: (b.key === '#ffffff' || b.key === 'gradient-light') ? '#333' : '#fff',
                    cursor: 'pointer', fontSize: 10, fontFamily: 'monospace',
                    minWidth: 32, textAlign: 'center' as const,
                  }}>
                    {b.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Panel layout */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 10, fontWeight: 700, fontFamily: 'monospace', color: muted, display: 'block', marginBottom: 6 }}>PANEL LAYOUT</label>
              <div style={{ display: 'flex', gap: 4 }}>
                {PANEL_LAYOUTS.map(l => (
                  <button key={l} onClick={() => setLayout(l)} style={{
                    padding: '4px 10px', background: layout === l ? `${accent}22` : card,
                    border: `1px solid ${layout === l ? accent : border}`,
                    borderRadius: 4, color: layout === l ? accent : muted,
                    cursor: 'pointer', fontSize: 11, fontFamily: 'monospace', fontWeight: 600,
                  }}>
                    {l}
                  </button>
                ))}
              </div>
            </div>

            {/* Rotation sync (multi-panel) */}
            {panels.length > 1 && (
              <div style={{ marginBottom: 16 }}>
                <button onClick={() => setRotationSync(!rotationSync)} style={{
                  width: '100%', padding: '5px 10px',
                  background: rotationSync ? `${green}22` : card,
                  border: `1px solid ${rotationSync ? green : border}`,
                  borderRadius: 6, color: rotationSync ? green : muted,
                  cursor: 'pointer', fontSize: 11, fontFamily: 'monospace', fontWeight: 600,
                }}>
                  {rotationSync ? 'Rotation Sync ON' : 'Rotation Sync OFF'}
                </button>
              </div>
            )}

            {/* Annotation tools */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 10, fontWeight: 700, fontFamily: 'monospace', color: muted, display: 'block', marginBottom: 6 }}>ANNOTATIONS</label>
              <div style={{ display: 'flex', gap: 4, marginBottom: 4, flexWrap: 'wrap' }}>
                <button onClick={() => setTool(tool === 'label' ? 'none' : 'label')} style={{
                  padding: '4px 10px', background: tool === 'label' ? `${green}33` : card,
                  border: `1px solid ${tool === 'label' ? green : border}`,
                  borderRadius: 4, color: tool === 'label' ? green : muted,
                  cursor: 'pointer', fontSize: 11, fontFamily: 'monospace',
                }}>
                  + Label
                </button>
                <button onClick={() => { setTool(tool === 'arrow' ? 'none' : 'arrow'); setArrowStart(null) }} style={{
                  padding: '4px 10px', background: tool === 'arrow' ? `${amber}33` : card,
                  border: `1px solid ${tool === 'arrow' ? amber : border}`,
                  borderRadius: 4, color: tool === 'arrow' ? amber : muted,
                  cursor: 'pointer', fontSize: 11, fontFamily: 'monospace',
                }}>
                  + Arrow
                </button>
                <button onClick={clearAnnotations} style={{
                  padding: '4px 10px', background: card,
                  border: `1px solid ${border}`, borderRadius: 4, color: red,
                  cursor: 'pointer', fontSize: 11, fontFamily: 'monospace',
                }}>
                  Clear
                </button>
              </div>
              <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
                <button onClick={() => setTool(tool === 'scale' ? 'none' : 'scale')} style={{
                  padding: '4px 10px', background: tool === 'scale' ? `${accent}33` : card,
                  border: `1px solid ${tool === 'scale' ? accent : border}`,
                  borderRadius: 4, color: tool === 'scale' ? accent : muted,
                  cursor: 'pointer', fontSize: 11, fontFamily: 'monospace',
                }}>
                  Scale Bar
                </button>
                <button onClick={() => { setTool(tool === 'measure' ? 'none' : 'measure'); setMeasureStart(null) }} style={{
                  padding: '4px 10px', background: tool === 'measure' ? `${accent}33` : card,
                  border: `1px solid ${tool === 'measure' ? accent : border}`,
                  borderRadius: 4, color: tool === 'measure' ? accent : muted,
                  cursor: 'pointer', fontSize: 11, fontFamily: 'monospace',
                }}>
                  Measure
                </button>
              </div>

              {/* Annotation text input */}
              <input
                value={labelText}
                onChange={e => setLabelText(e.target.value)}
                placeholder="Annotation text"
                style={{
                  width: '100%', padding: '4px 8px', background: card, border: `1px solid ${border}`,
                  borderRadius: 4, color: '#e2e8f0', fontSize: 12, fontFamily: 'monospace',
                  outline: 'none', marginBottom: 6, boxSizing: 'border-box',
                }}
              />

              {/* Color + size */}
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <input type="color" value={annColor} onChange={e => setAnnColor(e.target.value)}
                  style={{ width: 28, height: 28, border: 'none', background: 'transparent', cursor: 'pointer' }} />
                <input type="range" min={10} max={24} value={annFontSize} onChange={e => setAnnFontSize(Number(e.target.value))}
                  style={{ flex: 1, accentColor: accent }} />
                <span style={{ fontSize: 10, color: muted, fontFamily: 'monospace' }}>{annFontSize}px</span>
              </div>
            </div>

            {/* Tool status */}
            {tool !== 'none' && (
              <div style={{
                padding: '8px 10px', background: `${green}11`, border: `1px solid ${green}33`,
                borderRadius: 6, marginBottom: 16, fontSize: 11, color: green, fontFamily: 'monospace',
              }}>
                {tool === 'label' ? 'Click on figure to place label' :
                 tool === 'scale' ? 'Click on figure to place scale bar' :
                 tool === 'measure' ? (measureStart ? 'Click second point to measure' : 'Click first point to measure') :
                 arrowStart ? 'Click arrow end point' : 'Click arrow start point'}
              </div>
            )}

            {/* PDB metadata */}
            {pdbMeta && (
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 10, fontWeight: 700, fontFamily: 'monospace', color: muted, display: 'block', marginBottom: 6 }}>STRUCTURE INFO</label>
                <div style={{ padding: 8, background: card, border: `1px solid ${border}`, borderRadius: 6, fontSize: 11, fontFamily: 'monospace', lineHeight: 1.5 }}>
                  {pdbMeta.title && <div style={{ color: '#e2e8f0', marginBottom: 4 }}>{pdbMeta.title}</div>}
                  {pdbMeta.method && <div style={{ color: muted }}>Method: {pdbMeta.method}</div>}
                  {pdbMeta.resolution && <div style={{ color: muted }}>Resolution: {pdbMeta.resolution}</div>}
                  {pdbMeta.organism && <div style={{ color: muted }}>Organism: {pdbMeta.organism}</div>}
                </div>
              </div>
            )}

            {/* AI Analysis */}
            <div style={{ marginBottom: 16 }}>
              <button onClick={askAI} disabled={aiLoading || !ap?.pdbId} style={{
                width: '100%', padding: '6px 10px', background: `${accent}22`, border: `1px solid ${accent}44`,
                borderRadius: 6, color: accent, cursor: aiLoading ? 'wait' : 'pointer',
                fontSize: 11, fontFamily: 'monospace', fontWeight: 600,
                opacity: (!ap?.pdbId) ? 0.4 : 1,
              }}>
                {aiLoading ? 'Analyzing...' : 'AI Analysis'}
              </button>
              {aiResult && (
                <div style={{
                  marginTop: 8, padding: 8, background: card, border: `1px solid ${border}`,
                  borderRadius: 6, fontSize: 11, color: '#cbd5e1', lineHeight: 1.5,
                  maxHeight: 200, overflowY: 'auto',
                }}>
                  {aiResult}
                </div>
              )}
            </div>
          </div>

          {/* ── CENTER: Figure Panels ── */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

            {/* Figure title */}
            <div style={{ padding: '8px 16px', borderBottom: `1px solid ${border}` }}>
              <input
                value={figureTitle}
                onChange={e => setFigureTitle(e.target.value)}
                style={{
                  width: '100%', padding: '4px 8px', background: 'transparent', border: 'none',
                  color: '#e2e8f0', fontSize: 16, fontWeight: 700, outline: 'none',
                }}
                placeholder="Figure title..."
              />
            </div>

            {/* Panel grid */}
            <div id="figure-export-area" style={{
              flex: 1, display: 'grid',
              gridTemplateColumns: `repeat(${layoutGrid(layout).cols}, 1fr)`,
              gridTemplateRows: `repeat(${layoutGrid(layout).rows}, 1fr)`,
              gap: 4, padding: 4,
            }}>
              {panels.map((panel) => (
                <div key={panel.id}
                  onClick={() => setActivePanel(panel.id)}
                  onDrop={(e) => handleFileDrop(e, panel.id)}
                  onDragOver={handleDragOver}
                  style={{
                    position: 'relative',
                    border: `2px solid ${activePanel === panel.id ? accent : border}`,
                    borderRadius: 8,
                    overflow: 'hidden',
                    cursor: 'pointer',
                    minHeight: 300,
                  }}
                >
                  {/* Panel label */}
                  {panels.length > 1 && (
                    <div style={{
                      position: 'absolute', top: 6, left: 6, zIndex: 10,
                      background: 'rgba(0,0,0,0.6)', padding: '2px 8px', borderRadius: 4,
                      fontSize: 14, fontWeight: 700, fontFamily: 'monospace', color: '#fff',
                    }}>
                      {panel.label}
                    </div>
                  )}

                  {/* PDB ID badge */}
                  {panel.pdbId && (
                    <div style={{
                      position: 'absolute', top: 6, right: 6, zIndex: 10,
                      background: `${accent}44`, padding: '2px 6px', borderRadius: 4,
                      fontSize: 10, fontFamily: 'monospace', color: accent,
                    }}>
                      {panel.pdbId}
                    </div>
                  )}

                  {/* Loading indicator */}
                  {loading[panel.id] && (
                    <div style={{
                      position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                      zIndex: 10, color: muted, fontSize: 12, fontFamily: 'monospace',
                    }}>
                      Loading {panel.pdbId}...
                    </div>
                  )}

                  {/* 3Dmol container */}
                  <div
                    ref={el => { containerRefs.current[panel.id] = el }}
                    style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }}
                  />

                  {/* Empty state */}
                  {!panel.pdbId && (
                    <div style={{
                      position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                      textAlign: 'center', color: muted, fontSize: 12, fontFamily: 'monospace',
                    }}>
                      <div style={{ fontSize: 32, marginBottom: 8, opacity: 0.2 }}>+</div>
                      <div>Enter PDB ID or drop .pdb/.cif file</div>
                    </div>
                  )}

                  {/* SVG annotation overlay */}
                  <svg
                    style={{
                      position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
                      pointerEvents: tool !== 'none' ? 'all' : 'none',
                      zIndex: 5, cursor: tool === 'label' ? 'crosshair' : tool === 'arrow' ? 'crosshair' : 'default',
                    }}
                    onClick={(e) => handleSvgClick(e, panel.id)}
                    onMouseMove={(e) => handleSvgMouseMove(e, panel.id)}
                    onMouseUp={handleSvgMouseUp}
                  >
                    {/* Arrow marker */}
                    <defs>
                      <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
                        <polygon points="0 0, 8 3, 0 6" fill={annColor} />
                      </marker>
                    </defs>

                    {panel.annotations.map(ann => (
                      <g key={ann.id}>
                        {ann.type === 'label' && (
                          <g
                            style={{ pointerEvents: 'all', cursor: 'move' }}
                            onMouseDown={(e) => handleAnnMouseDown(e, ann.id, panel.id)}
                            onDoubleClick={(e) => { e.stopPropagation(); deleteAnnotation(ann.id, panel.id) }}
                          >
                            <rect
                              x={ann.x - 2} y={ann.y - ann.fontSize}
                              width={ann.text.length * ann.fontSize * 0.62 + 8}
                              height={ann.fontSize + 6}
                              fill="rgba(0,0,0,0.7)" rx={3}
                            />
                            <text
                              x={ann.x + 2} y={ann.y - 2}
                              fill={ann.color} fontSize={ann.fontSize}
                              fontWeight="bold" fontFamily="system-ui, sans-serif"
                            >
                              {ann.text}
                            </text>
                          </g>
                        )}
                        {ann.type === 'arrow' && ann.targetX !== undefined && ann.targetY !== undefined && (
                          <g
                            style={{ pointerEvents: 'all', cursor: 'move' }}
                            onMouseDown={(e) => handleAnnMouseDown(e, ann.id, panel.id)}
                            onDoubleClick={(e) => { e.stopPropagation(); deleteAnnotation(ann.id, panel.id) }}
                          >
                            <line
                              x1={ann.x} y1={ann.y}
                              x2={ann.targetX} y2={ann.targetY}
                              stroke={ann.color} strokeWidth={2}
                              markerEnd="url(#arrowhead)"
                            />
                            {ann.text && (
                              <>
                                <rect
                                  x={ann.x - 2} y={ann.y - ann.fontSize - 4}
                                  width={ann.text.length * ann.fontSize * 0.62 + 8}
                                  height={ann.fontSize + 4}
                                  fill="rgba(0,0,0,0.6)" rx={3}
                                />
                                <text
                                  x={ann.x + 2} y={ann.y - 6}
                                  fill={ann.color} fontSize={ann.fontSize}
                                  fontWeight="bold" fontFamily="system-ui, sans-serif"
                                >
                                  {ann.text}
                                </text>
                              </>
                            )}
                          </g>
                        )}
                        {/* Scale bar */}
                        {ann.type === 'scale' && ann.targetX !== undefined && ann.targetY !== undefined && (
                          <g
                            style={{ pointerEvents: 'all', cursor: 'move' }}
                            onMouseDown={(e) => handleAnnMouseDown(e, ann.id, panel.id)}
                            onDoubleClick={(e) => { e.stopPropagation(); deleteAnnotation(ann.id, panel.id) }}
                          >
                            {/* Main bar */}
                            <line x1={ann.x} y1={ann.y} x2={ann.targetX} y2={ann.targetY}
                              stroke={ann.color} strokeWidth={3} />
                            {/* End ticks */}
                            <line x1={ann.x} y1={ann.y - 5} x2={ann.x} y2={ann.y + 5}
                              stroke={ann.color} strokeWidth={2} />
                            <line x1={ann.targetX} y1={ann.targetY - 5} x2={ann.targetX} y2={ann.targetY + 5}
                              stroke={ann.color} strokeWidth={2} />
                            {/* Label */}
                            <rect
                              x={(ann.x + ann.targetX) / 2 - ann.text.length * ann.fontSize * 0.31 - 4}
                              y={ann.y - ann.fontSize - 6}
                              width={ann.text.length * ann.fontSize * 0.62 + 8}
                              height={ann.fontSize + 4}
                              fill="rgba(0,0,0,0.7)" rx={3}
                            />
                            <text
                              x={(ann.x + ann.targetX) / 2}
                              y={ann.y - ann.fontSize / 2 + 1}
                              fill={ann.color} fontSize={ann.fontSize}
                              fontWeight="bold" fontFamily="system-ui, sans-serif"
                              textAnchor="middle"
                            >
                              {ann.text}
                            </text>
                          </g>
                        )}
                        {/* Measurement line */}
                        {ann.type === 'measure' && ann.targetX !== undefined && ann.targetY !== undefined && (
                          <g
                            style={{ pointerEvents: 'all', cursor: 'move' }}
                            onMouseDown={(e) => handleAnnMouseDown(e, ann.id, panel.id)}
                            onDoubleClick={(e) => { e.stopPropagation(); deleteAnnotation(ann.id, panel.id) }}
                          >
                            {/* Dashed measurement line */}
                            <line x1={ann.x} y1={ann.y} x2={ann.targetX} y2={ann.targetY}
                              stroke={ann.color} strokeWidth={1.5} strokeDasharray="4 3" />
                            {/* Endpoint dots */}
                            <circle cx={ann.x} cy={ann.y} r={3} fill={ann.color} />
                            <circle cx={ann.targetX} cy={ann.targetY} r={3} fill={ann.color} />
                            {/* Distance label at midpoint */}
                            <rect
                              x={(ann.x + ann.targetX) / 2 - ann.text.length * ann.fontSize * 0.31 - 4}
                              y={(ann.y + ann.targetY) / 2 - ann.fontSize}
                              width={ann.text.length * ann.fontSize * 0.62 + 8}
                              height={ann.fontSize + 4}
                              fill="rgba(0,0,0,0.8)" rx={3}
                            />
                            <text
                              x={(ann.x + ann.targetX) / 2}
                              y={(ann.y + ann.targetY) / 2 - ann.fontSize / 2 + 5}
                              fill={ann.color} fontSize={ann.fontSize}
                              fontWeight="bold" fontFamily="system-ui, sans-serif"
                              textAnchor="middle"
                            >
                              {ann.text}
                            </text>
                          </g>
                        )}
                      </g>
                    ))}

                    {/* Arrow preview dot */}
                    {tool === 'arrow' && arrowStart && (
                      <circle cx={arrowStart.x} cy={arrowStart.y} r={4} fill={green} opacity={0.8} />
                    )}
                    {/* Measure preview dot */}
                    {tool === 'measure' && measureStart && (
                      <circle cx={measureStart.x} cy={measureStart.y} r={4} fill={accent} opacity={0.8} />
                    )}
                  </svg>
                </div>
              ))}
            </div>

            {/* Caption */}
            <div style={{ padding: '8px 16px', borderTop: `1px solid ${border}` }}>
              <textarea
                value={caption}
                onChange={e => setCaption(e.target.value)}
                placeholder="Figure caption — describe the molecular structures, experimental conditions, and key observations..."
                rows={2}
                style={{
                  width: '100%', padding: '6px 10px', background: card, border: `1px solid ${border}`,
                  borderRadius: 6, color: '#94a3b8', fontSize: 12, fontFamily: 'system-ui, sans-serif',
                  outline: 'none', resize: 'vertical', lineHeight: 1.5, boxSizing: 'border-box',
                }}
              />
            </div>
          </div>
        </div>
      ) : (
        /* ── ARTICLE MODE ── */
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 24px' }}>
          <div style={{ marginBottom: 24 }}>
            <input
              value={sections.find(s => s.id === 'title')?.content || ''}
              onChange={e => setSections(prev => prev.map(s => s.id === 'title' ? { ...s, content: e.target.value } : s))}
              placeholder="Article Title"
              style={{
                width: '100%', padding: '8px 0', background: 'transparent', border: 'none',
                borderBottom: `1px solid ${border}`, color: '#e2e8f0', fontSize: 28, fontWeight: 700,
                outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Abstract */}
          <div style={{ marginBottom: 24 }}>
            <label style={{ fontSize: 11, fontWeight: 700, fontFamily: 'monospace', color: accent, display: 'block', marginBottom: 6 }}>ABSTRACT</label>
            <textarea
              value={sections.find(s => s.id === 'abstract')?.content || ''}
              onChange={e => setSections(prev => prev.map(s => s.id === 'abstract' ? { ...s, content: e.target.value } : s))}
              placeholder="Brief summary of the work..."
              rows={6}
              style={{
                width: '100%', padding: '12px 16px', background: card, border: `1px solid ${border}`,
                borderRadius: 8, color: '#e2e8f0', fontSize: 14, lineHeight: 1.7,
                outline: 'none', resize: 'vertical', fontFamily: 'Georgia, "Times New Roman", serif',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Body */}
          <div style={{ marginBottom: 24 }}>
            <label style={{ fontSize: 11, fontWeight: 700, fontFamily: 'monospace', color: accent, display: 'block', marginBottom: 6 }}>BODY</label>
            <textarea
              value={sections.find(s => s.id === 'body')?.content || ''}
              onChange={e => setSections(prev => prev.map(s => s.id === 'body' ? { ...s, content: e.target.value } : s))}
              placeholder="Article body — use Markdown for formatting. Reference figures as (Fig. 1), (Fig. 2A)..."
              rows={20}
              style={{
                width: '100%', padding: '12px 16px', background: card, border: `1px solid ${border}`,
                borderRadius: 8, color: '#e2e8f0', fontSize: 14, lineHeight: 1.7,
                outline: 'none', resize: 'vertical', fontFamily: 'Georgia, "Times New Roman", serif',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Add current figure to reference list */}
          <div style={{ marginBottom: 24, display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={addFigureRef} style={{
              padding: '6px 14px', background: `${accent}22`, border: `1px solid ${accent}44`,
              borderRadius: 6, color: accent, cursor: 'pointer',
              fontSize: 12, fontFamily: 'monospace', fontWeight: 600,
            }}>
              + Add Fig. {figureCounter} Reference
            </button>
            <span style={{ fontSize: 11, color: muted, fontFamily: 'monospace' }}>
              (Registers current figure title and caption)
            </span>
          </div>

          {/* Figure reference list */}
          {figureRefs.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              <label style={{ fontSize: 11, fontWeight: 700, fontFamily: 'monospace', color: accent, display: 'block', marginBottom: 6 }}>FIGURE LIST</label>
              <div style={{ padding: 12, background: card, border: `1px solid ${border}`, borderRadius: 8 }}>
                {figureRefs.map((ref, i) => (
                  <div key={i} style={{
                    display: 'flex', gap: 8, alignItems: 'baseline',
                    padding: '4px 0', borderBottom: i < figureRefs.length - 1 ? `1px solid ${border}` : 'none',
                  }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: accent, fontFamily: 'monospace', whiteSpace: 'nowrap' as const }}>
                      Fig. {ref.num}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0' }}>{ref.title}</div>
                      {ref.caption && (
                        <div style={{ fontSize: 11, color: muted, marginTop: 2 }}>{ref.caption.substring(0, 100)}{ref.caption.length > 100 ? '...' : ''}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Figure reference hint */}
          <div style={{
            padding: '12px 16px', background: `${accent}08`, border: `1px solid ${accent}22`,
            borderRadius: 8, fontSize: 12, color: muted, fontFamily: 'monospace', lineHeight: 1.6,
          }}>
            Switch to Figure mode to create molecular figures. Use &quot;+ Add Fig. Reference&quot; to register each figure.
            Reference them in your text as (Fig. 1A), (Fig. 1B), etc.
          </div>
        </div>
      )}
    </div>
  )
}
