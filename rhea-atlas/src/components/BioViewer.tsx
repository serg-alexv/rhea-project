'use client'

import { useEffect, useRef, useState, useCallback } from 'react'

const API = process.env.NEXT_PUBLIC_CC_API ?? 'http://localhost:8400'

const PDB_PRESETS = [
  { id: '1CRN', name: 'Crambin' },
  { id: '1BNA', name: 'DNA B-form' },
  { id: '4HHB', name: 'Hemoglobin' },
  { id: '1ATP', name: 'ATP synthase' },
  { id: '6LU7', name: 'SARS-CoV-2' },
  { id: '1GZM', name: 'GFP' },
]

const SMILES_PRESETS = [
  { name: 'Aspirin', smiles: 'CC(=O)Oc1ccccc1C(=O)O' },
  { name: 'Caffeine', smiles: 'Cn1cnc2c1c(=O)n(C)c(=O)n2C' },
  { name: 'Dopamine', smiles: 'NCCc1ccc(O)c(O)c1' },
  { name: 'Glucose', smiles: 'OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O' },
]

const STYLES = ['cartoon', 'stick', 'sphere', 'line', 'cross']
const COLORS = ['spectrum', 'chain', 'ss', 'element', 'residue']

function isSMILES(input: string): boolean {
  const trimmed = input.trim()
  if (trimmed.length === 4 && /^[A-Za-z0-9]+$/.test(trimmed)) return false
  if (/[=\#\(\)@\/\\\[\]\+\-\%]/.test(trimmed)) return true
  if (/[cnosp]/.test(trimmed)) return true
  if (trimmed.length > 6 && !/^[A-Za-z0-9]+$/.test(trimmed)) return true
  return false
}

function buildViewerHTML(moleculeID: string, isSmiles: boolean, style: string, colorScheme: string): string {
  const colorMap: Record<string, string> = {
    chain: '{colorfunc: $3Dmol.chainHetatmColorFunc}',
    ss: "{colorscheme: 'ssJmol'}",
    element: "{colorscheme: 'default'}",
    residue: "{colorscheme: 'amino'}",
    spectrum: "{color: 'spectrum'}",
  }
  const colorJS = colorMap[colorScheme] || colorMap.spectrum

  const styleMap: Record<string, string> = {
    stick: `viewer.setStyle({}, {stick: ${colorJS}});`,
    sphere: `viewer.setStyle({}, {sphere: {scale: 0.3, ${colorJS.slice(1, -1)}}});`,
    line: `viewer.setStyle({}, {line: ${colorJS}});`,
    cross: `viewer.setStyle({}, {cross: {linewidth: 2, ${colorJS.slice(1, -1)}}});`,
    cartoon: `viewer.setStyle({}, {cartoon: ${colorJS}});`,
  }
  const styleJS = styleMap[style] || styleMap.cartoon

  const escaped = moleculeID.replace(/\\/g, '\\\\').replace(/'/g, "\\'")

  const loadJS = isSmiles
    ? `try {
        viewer.addModel('${escaped}', 'smi');
        ${styleJS}
        viewer.zoomTo(); viewer.render();
        document.getElementById('loading').style.display = 'none';
        var atoms = viewer.getModel().selectedAtoms({});
        document.getElementById('info').textContent = 'SMILES — ' + atoms.length + ' atoms';
      } catch(e) {
        document.getElementById('loading').textContent = 'Error: ' + e.message;
        document.getElementById('loading').style.color = '#ff6b6b';
      }`
    : `$3Dmol.download('pdb:${escaped}', viewer, {}, function() {
        ${styleJS}
        viewer.zoomTo(); viewer.render();
        document.getElementById('loading').style.display = 'none';
        var atoms = viewer.getModel().selectedAtoms({});
        document.getElementById('info').textContent = '${escaped} — ' + atoms.length + ' atoms';
      });`

  return `<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<style>
  *{margin:0;padding:0}
  body{background:#0f0f1a;overflow:hidden}
  #viewer{width:100vw;height:100vh;position:relative}
  #info{position:absolute;bottom:8px;left:8px;color:rgba(255,255,255,0.5);font:10px/1.2 monospace;pointer-events:none}
  #loading{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:rgba(102,217,255,0.8);font:14px monospace;text-align:center}
</style>
<script src="https://3dmol.org/build/3Dmol-min.js"></script>
</head><body>
<div id="viewer"></div>
<div id="info">${isSmiles ? 'SMILES' : moleculeID}</div>
<div id="loading">Loading ${isSmiles ? 'SMILES' : moleculeID}...</div>
<script>
  var viewer = $3Dmol.createViewer("viewer",{backgroundColor:"0x0f0f1a",antialias:true});
  ${loadJS}
</script>
</body></html>`
}

interface BioMeta {
  title?: string
  method?: string
  resolution?: string
  organism?: string
}

export default function BioViewer() {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [search, setSearch] = useState('')
  const [moleculeID, setMoleculeID] = useState('1CRN')
  const [isSmiles, setIsSmiles] = useState(false)
  const [style, setStyle] = useState('cartoon')
  const [color, setColor] = useState('spectrum')
  const [meta, setMeta] = useState<BioMeta>({})
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)

  const loadMolecule = useCallback((id: string, smiles: boolean) => {
    setMoleculeID(id)
    setIsSmiles(smiles)
    setAnalysis(null)
    setMeta({})
    if (!smiles) {
      fetch(`${API}/bio/lookup?q=${id}`)
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          if (d && !d.error) {
            setMeta({
              title: d.title,
              method: d.experimental_method?.substring(0, 4).toUpperCase(),
              resolution: typeof d.resolution_angstrom === 'number'
                ? d.resolution_angstrom.toFixed(2) : d.resolution_angstrom,
              organism: d.organism,
            })
          }
        })
        .catch(() => {})
    }
  }, [])

  const handleSearch = () => {
    const raw = search.trim()
    if (!raw) return
    if (isSMILES(raw)) {
      loadMolecule(raw, true)
    } else {
      loadMolecule(raw.toUpperCase(), false)
    }
  }

  const askAbout = async () => {
    setAnalysisLoading(true)
    setAnalysis(null)
    const prompt = isSmiles
      ? `Describe the biological significance of this molecule (SMILES: ${moleculeID}). Include: chemical class, pharmacological activity, key functional groups, common research uses.`
      : `Describe the biological significance of ${moleculeID}. Include: protein function, common uses in biochemistry research, key binding sites, structural highlights.`

    try {
      const res = await fetch(`${API}/keyboard/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: prompt, action: 'freeform' }),
      })
      const data = await res.json()
      setAnalysis(data.text || data.result || JSON.stringify(data))
    } catch (e) {
      setAnalysis('Error: could not reach API')
    } finally {
      setAnalysisLoading(false)
    }
  }

  const html = buildViewerHTML(moleculeID, isSmiles, style, color)

  return (
    <div className="absolute inset-0 flex flex-col bg-[#0f0f1a]">
      {/* Control bar */}
      <div className="shrink-0 border-b border-white/[0.06] bg-black/40 px-3 py-2 space-y-2">
        {/* Search + presets */}
        <div className="flex items-center gap-2 flex-wrap">
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="PDB ID or SMILES..."
            className="bg-black/50 border border-white/10 rounded px-2 py-1 text-xs text-white/80 w-36 font-mono placeholder:text-white/20"
          />
          <button onClick={handleSearch} className="px-2 py-1 bg-cyan-500/20 border border-cyan-500/30 rounded text-[10px] text-cyan-400 font-mono">
            Load
          </button>
          <div className="h-3 w-px bg-white/10" />
          {PDB_PRESETS.map(p => (
            <button key={p.id} onClick={() => { loadMolecule(p.id, false); setSearch(p.id) }}
              className={`px-2 py-0.5 rounded text-[9px] font-mono transition-colors ${
                moleculeID === p.id && !isSmiles ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'text-white/30 hover:text-white/50'
              }`}>
              {p.name}
            </button>
          ))}
          <div className="h-3 w-px bg-white/10" />
          {SMILES_PRESETS.map(p => (
            <button key={p.name} onClick={() => { loadMolecule(p.smiles, true); setSearch(p.smiles) }}
              className={`px-2 py-0.5 rounded text-[9px] font-mono transition-colors ${
                moleculeID === p.smiles && isSmiles ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'text-white/30 hover:text-white/50'
              }`}>
              {p.name}
            </button>
          ))}
        </div>

        {/* Style + color + ask */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[9px] font-bold text-white/30 font-mono w-10">STYLE</span>
          {STYLES.map(s => (
            <button key={s} onClick={() => setStyle(s)}
              className={`px-2 py-0.5 rounded text-[9px] font-mono ${
                style === s ? 'bg-emerald-500/20 text-emerald-400' : 'text-white/30 hover:text-white/50'
              }`}>
              {s}
            </button>
          ))}
          <div className="h-3 w-px bg-white/10" />
          <span className="text-[9px] font-bold text-white/30 font-mono w-10">COLOR</span>
          {COLORS.map(c => (
            <button key={c} onClick={() => setColor(c)}
              className={`px-2 py-0.5 rounded text-[9px] font-mono ${
                color === c ? 'bg-amber-500/20 text-amber-400' : 'text-white/30 hover:text-white/50'
              }`}>
              {c.substring(0, 4)}
            </button>
          ))}
          <div className="h-3 w-px bg-white/10" />
          <button onClick={askAbout} disabled={analysisLoading}
            className="px-2 py-0.5 bg-violet-500/20 border border-violet-500/30 rounded text-[9px] text-violet-400 font-mono disabled:opacity-40">
            {analysisLoading ? 'Analyzing...' : 'Ask about this molecule'}
          </button>
        </div>

        {/* Meta tags */}
        {(meta.title || meta.method || meta.resolution || meta.organism) && (
          <div className="flex items-center gap-2 flex-wrap">
            {meta.title && <span className="text-[9px] text-white/50 font-mono">{meta.title}</span>}
            {meta.method && <span className="px-1.5 py-0.5 bg-cyan-500/10 rounded text-[9px] text-cyan-400/60 font-mono">{meta.method}</span>}
            {meta.resolution && <span className="px-1.5 py-0.5 bg-cyan-500/10 rounded text-[9px] text-cyan-400/60 font-mono">{meta.resolution}A</span>}
            {meta.organism && <span className="text-[9px] text-white/30 font-mono italic">{meta.organism}</span>}
          </div>
        )}
      </div>

      {/* 3D Viewer iframe */}
      <div className="flex-1 relative">
        <iframe
          ref={iframeRef}
          srcDoc={html}
          className="absolute inset-0 w-full h-full border-0"
          sandbox="allow-scripts allow-same-origin"
          title="3Dmol Viewer"
        />
      </div>

      {/* Analysis panel */}
      {(analysis || analysisLoading) && (
        <div className="shrink-0 border-t border-violet-500/20 bg-violet-500/5 px-3 py-2 max-h-40 overflow-y-auto">
          <div className="text-[9px] font-bold uppercase tracking-widest text-violet-400 mb-1">Analysis</div>
          <div className="text-xs text-white/60 font-mono leading-relaxed whitespace-pre-wrap">
            {analysisLoading ? 'Querying tribunal...' : analysis}
          </div>
        </div>
      )}
    </div>
  )
}
