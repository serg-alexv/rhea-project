'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import Link from 'next/link'

// ─── Symbol Palettes ─────────────────────────────────────────────────

const PALETTES: Record<string, { label: string; symbols: string[] }> = {
  greek_lower: {
    label: 'α–ω',
    symbols: 'α β γ δ ε ζ η θ ι κ λ μ ν ξ π ρ σ τ υ φ χ ψ ω'.split(' '),
  },
  greek_upper: {
    label: 'Α–Ω',
    symbols: 'Α Β Γ Δ Ε Ζ Η Θ Ι Κ Λ Μ Ν Ξ Π Ρ Σ Τ Υ Φ Χ Ψ Ω'.split(' '),
  },
  logic: {
    label: '∧∨¬',
    symbols: '∧ ∨ ¬ → ← ↔ ⊕ ∀ ∃ ∄ ⊤ ⊥ ⊢ ⊨ ⊬ ⊭'.split(' '),
  },
  sets: {
    label: '∈∪',
    symbols: '∈ ∉ ⊂ ⊃ ⊆ ⊇ ∪ ∩ ∅ ℕ ℤ ℚ ℝ ℂ ∖ △'.split(' '),
  },
  math: {
    label: '∑∫',
    symbols: '∑ ∏ ∫ ∂ ∞ √ ≈ ≠ ≤ ≥ ± × ÷ · ° ‰'.split(' '),
  },
  arrows: {
    label: '⇒↦',
    symbols: '⇒ ⇐ ⇔ ↦ ↣ ↠ ⟶ ⟵ ⟷ ↑ ↓ ↕ ⇑ ⇓ ⇕ ↗'.split(' '),
  },
  brackets: {
    label: '⟨⟩',
    symbols: '( ) [ ] { } ⟨ ⟩ ⌈ ⌉ ⌊ ⌋ | ‖ ⟦ ⟧'.split(' '),
  },
  subscript: {
    label: 'x₁',
    symbols: '₀ ₁ ₂ ₃ ₄ ₅ ₆ ₇ ₈ ₉ ₊ ₋ ₌ ₍ ₎ ₙ'.split(' '),
  },
  superscript: {
    label: 'x²',
    symbols: '⁰ ¹ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ⁺ ⁻ ⁼ ⁽ ⁾ ⁿ'.split(' '),
  },
}

// ─── Templates — common logical forms ────────────────────────────────

const TEMPLATES = [
  { label: 'Modus Ponens',      formula: '(P → Q) ∧ P ⊢ Q' },
  { label: 'Modus Tollens',     formula: '(P → Q) ∧ ¬Q ⊢ ¬P' },
  { label: 'DeMorgan 1',        formula: '¬(P ∧ Q) ↔ (¬P ∨ ¬Q)' },
  { label: 'DeMorgan 2',        formula: '¬(P ∨ Q) ↔ (¬P ∧ ¬Q)' },
  { label: 'Universal Inst.',   formula: '∀x P(x) → P(a)' },
  { label: 'Existential Gen.',  formula: 'P(a) → ∃x P(x)' },
  { label: 'Contrapositive',    formula: '(P → Q) ↔ (¬Q → ¬P)' },
  { label: 'Double Negation',   formula: '¬¬P ↔ P' },
  { label: 'Distributive ∧/∨',  formula: 'P ∧ (Q ∨ R) ↔ (P ∧ Q) ∨ (P ∧ R)' },
  { label: 'Absorption',        formula: 'P ∧ (P ∨ Q) ↔ P' },
  { label: 'Excluded Middle',   formula: 'P ∨ ¬P' },
  { label: 'Contradiction',     formula: '¬(P ∧ ¬P)' },
]

// ─── Styles ──────────────────────────────────────────────────────────

const bg = '#0a0a0f'
const card = '#111118'
const border = '#1e1e2e'
const accent = '#6366f1'
const green = '#22c55e'
const muted = '#64748b'

// ─── Page Component ──────────────────────────────────────────────────

export default function LogicPage() {
  const [formula, setFormula] = useState('')
  const [cursorPos, setCursorPos] = useState(0)
  const [activePalette, setActivePalette] = useState<string>('logic')
  const [history, setHistory] = useState<string[]>([])
  const [copied, setCopied] = useState(false)
  const [showTemplates, setShowTemplates] = useState(false)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Restore history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('rhea-logic-history')
    if (saved) {
      try { setHistory(JSON.parse(saved)) } catch { /* ignore */ }
    }
  }, [])

  const saveHistory = useCallback((h: string[]) => {
    setHistory(h)
    localStorage.setItem('rhea-logic-history', JSON.stringify(h.slice(0, 50)))
  }, [])

  const insertSymbol = useCallback((sym: string) => {
    setFormula(prev => {
      const pos = inputRef.current?.selectionStart ?? prev.length
      const next = prev.slice(0, pos) + sym + prev.slice(pos)
      // Set cursor after inserted symbol on next tick
      setTimeout(() => {
        if (inputRef.current) {
          const newPos = pos + sym.length
          inputRef.current.selectionStart = newPos
          inputRef.current.selectionEnd = newPos
          inputRef.current.focus()
        }
      }, 0)
      return next
    })
  }, [])

  const copyFormula = useCallback(() => {
    navigator.clipboard.writeText(formula).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }, [formula])

  const pushToHistory = useCallback(() => {
    if (!formula.trim()) return
    const next = [formula, ...history.filter(h => h !== formula)].slice(0, 50)
    saveHistory(next)
  }, [formula, history, saveHistory])

  const clearFormula = useCallback(() => {
    if (formula.trim()) pushToHistory()
    setFormula('')
    inputRef.current?.focus()
  }, [formula, pushToHistory])

  const loadTemplate = useCallback((t: string) => {
    if (formula.trim()) pushToHistory()
    setFormula(t)
    setShowTemplates(false)
    inputRef.current?.focus()
  }, [formula, pushToHistory])

  const BRACKET_PAIRS: Record<string, string> = {
    '(': ')', '[': ']', '{': '}', '⟨': '⟩', '⌈': '⌉', '⌊': '⌋', '⟦': '⟧',
  }
  const CLOSE_SET = Object.values(BRACKET_PAIRS)
  const OPEN_SET = Object.keys(BRACKET_PAIRS)
  const BINARY_LIST = '∧ ∨ → ← ↔ ⊕ ⊢ ⊨ ⇒ ⇐ ⇔ ∈ ∉ ⊂ ⊃ ⊆ ⊇ ∪ ∩ ∖ × ≈ ≠ ≤ ≥ ± · ÷'.split(' ')
  const UNARY_LIST = ['¬', '∀', '∃', '∄']
  const ALL_OPS_LIST = BINARY_LIST.concat(UNARY_LIST)
  const isBinary = (c: string) => BINARY_LIST.includes(c)
  const isUnary = (c: string) => UNARY_LIST.includes(c)
  const isOp = (c: string) => ALL_OPS_LIST.includes(c)
  const isOpen = (c: string) => OPEN_SET.includes(c)
  const isClose = (c: string) => CLOSE_SET.includes(c)

  function evaluateFormula(input: string): { valid: boolean; normalized?: string; error?: string } {
    const s = input.trim()
    if (!s) return { valid: false, error: 'Empty formula' }

    // 1. Bracket balance
    const stack: string[] = []
    for (let i = 0; i < s.length; i++) {
      const ch = s[i]
      if (isOpen(ch)) {
        stack.push(ch)
      } else if (isClose(ch)) {
        const last = stack.pop()
        if (!last || BRACKET_PAIRS[last] !== ch) {
          return { valid: false, error: `Unmatched '${ch}' at position ${i + 1}` }
        }
      }
    }
    if (stack.length > 0) {
      return { valid: false, error: `Unclosed '${stack[stack.length - 1]}'` }
    }

    // 2. Tokenize for operator validation
    const tokens: string[] = []
    let buf = ''
    for (const ch of s) {
      if (ch === ' ') {
        if (buf) { tokens.push(buf); buf = '' }
        continue
      }
      if (isOp(ch) || isOpen(ch) || isClose(ch) || ch === '|' || ch === '‖') {
        if (buf) { tokens.push(buf); buf = '' }
        tokens.push(ch)
      } else {
        buf += ch
      }
    }
    if (buf) tokens.push(buf)

    // 3. Operator position checks
    for (let i = 0; i < tokens.length; i++) {
      const t = tokens[i]
      if (isBinary(t)) {
        if (i === 0) return { valid: false, error: `Binary operator '${t}' at start` }
        if (i === tokens.length - 1) return { valid: false, error: `Binary operator '${t}' at end` }
        const prev = tokens[i - 1]
        if (isBinary(prev) || isUnary(prev)) {
          return { valid: false, error: `Adjacent operators '${prev}' and '${t}'` }
        }
      }
    }

    // 4. Normalize: single space around binary ops, trim
    let norm = s
    for (let bi = 0; bi < BINARY_LIST.length; bi++) {
      const op = BINARY_LIST[bi]
      norm = norm.split(op).map(p => p.trim()).join(` ${op} `)
    }
    norm = norm.replace(/  +/g, ' ').trim()

    return { valid: true, normalized: norm }
  }

  const [evalResult, setEvalResult] = useState<{ valid: boolean; normalized?: string; error?: string } | null>(null)

  const runEvaluate = useCallback(() => {
    if (!formula.trim()) return
    const result = evaluateFormula(formula)
    setEvalResult(result)
    if (result.valid && result.normalized) {
      setFormula(result.normalized)
    }
    pushToHistory()
  }, [formula, pushToHistory])

  return (
    <div style={{ minHeight: '100vh', background: bg, color: '#e2e8f0', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* ─── Header ─── */}
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 24px', borderBottom: `1px solid ${border}` }}>
        <Link href="/cc" style={{ color: muted, textDecoration: 'none', fontSize: 13 }}>cc</Link>
        <span style={{ color: muted }}>/</span>
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, fontFamily: 'monospace', letterSpacing: 1 }}>
          <span style={{ color: accent }}>Thea</span> Logic
        </h1>
        <div style={{ flex: 1 }} />
        <button
          onClick={() => setShowTemplates(!showTemplates)}
          style={{
            background: showTemplates ? `${accent}33` : 'transparent',
            border: `1px solid ${showTemplates ? accent : border}`,
            color: showTemplates ? accent : muted,
            borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 12,
            fontFamily: 'monospace',
          }}
        >
          Templates
        </button>
      </header>

      <div style={{ display: 'flex', gap: 0, height: 'calc(100vh - 57px)' }}>
        {/* ─── Main Area ─── */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 20, gap: 16 }}>

          {/* ─── Formula Display ─── */}
          <div style={{
            background: card, border: `1px solid ${border}`, borderRadius: 12,
            padding: 20, minHeight: 120, position: 'relative',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 11, color: muted, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 1 }}>
                Formula
              </span>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  onClick={runEvaluate}
                  disabled={!formula}
                  style={{
                    background: evalResult?.valid ? `${green}22` : evalResult?.error ? '#ef444422' : `${accent}18`,
                    border: `1px solid ${evalResult?.valid ? green : evalResult?.error ? '#ef4444' : accent}`,
                    color: evalResult?.valid ? green : evalResult?.error ? '#ef4444' : accent,
                    borderRadius: 6, padding: '4px 10px', cursor: formula ? 'pointer' : 'default',
                    fontSize: 11, fontFamily: 'monospace', opacity: formula ? 1 : 0.4,
                  }}
                >
                  Evaluate
                </button>
                <button
                  onClick={copyFormula}
                  disabled={!formula}
                  style={{
                    background: copied ? `${green}22` : 'transparent',
                    border: `1px solid ${copied ? green : border}`,
                    color: copied ? green : muted,
                    borderRadius: 6, padding: '4px 10px', cursor: formula ? 'pointer' : 'default',
                    fontSize: 11, fontFamily: 'monospace', opacity: formula ? 1 : 0.4,
                  }}
                >
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  onClick={clearFormula}
                  disabled={!formula}
                  style={{
                    background: 'transparent', border: `1px solid ${border}`,
                    color: muted, borderRadius: 6, padding: '4px 10px', cursor: formula ? 'pointer' : 'default',
                    fontSize: 11, fontFamily: 'monospace', opacity: formula ? 1 : 0.4,
                  }}
                >
                  Clear
                </button>
              </div>
            </div>

            {/* Rendered formula (large, styled) */}
            <div style={{
              fontSize: 28, fontFamily: '"Cambria Math", "STIX Two Math", serif',
              letterSpacing: 1.5, lineHeight: 1.6, minHeight: 44,
              color: formula ? '#f1f5f9' : '#334155',
              wordBreak: 'break-word',
            }}>
              {formula || '∀x ∈ ℝ : P(x) → Q(x)'}
            </div>

            {/* Eval feedback */}
            {evalResult && (
              <div style={{
                fontSize: 12, fontFamily: 'monospace', marginTop: 6,
                color: evalResult.valid ? green : '#ef4444',
                padding: '4px 8px', borderRadius: 4,
                background: evalResult.valid ? `${green}11` : '#ef444411',
              }}>
                {evalResult.valid ? 'Valid — normalized' : evalResult.error}
              </div>
            )}

            {/* Editable input */}
            <textarea
              ref={inputRef}
              value={formula}
              onChange={e => { setFormula(e.target.value); setEvalResult(null) }}
              onSelect={e => setCursorPos((e.target as HTMLTextAreaElement).selectionStart)}
              placeholder="Type or click symbols below..."
              spellCheck={false}
              style={{
                width: '100%', marginTop: 12, background: '#0d0d14', border: `1px solid ${border}`,
                borderRadius: 8, padding: '10px 12px', color: '#cbd5e1', fontSize: 14,
                fontFamily: '"Fira Code", "SF Mono", monospace', resize: 'vertical',
                minHeight: 48, outline: 'none',
              }}
              onFocus={e => e.target.style.borderColor = accent}
              onBlur={e => e.target.style.borderColor = border}
            />
          </div>

          {/* ─── Symbol Palette ─── */}
          <div style={{ background: card, border: `1px solid ${border}`, borderRadius: 12, overflow: 'hidden' }}>
            {/* Palette tabs */}
            <div style={{
              display: 'flex', gap: 0, borderBottom: `1px solid ${border}`,
              overflowX: 'auto', scrollbarWidth: 'none',
            }}>
              {Object.entries(PALETTES).map(([key, pal]) => (
                <button
                  key={key}
                  onClick={() => setActivePalette(key)}
                  style={{
                    background: activePalette === key ? `${accent}22` : 'transparent',
                    border: 'none',
                    borderBottom: activePalette === key ? `2px solid ${accent}` : '2px solid transparent',
                    color: activePalette === key ? accent : muted,
                    padding: '8px 14px', cursor: 'pointer', fontSize: 13,
                    fontFamily: '"Cambria Math", serif', whiteSpace: 'nowrap',
                    transition: 'all 0.15s',
                  }}
                >
                  {pal.label}
                </button>
              ))}
            </div>

            {/* Symbol grid */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(44px, 1fr))',
              gap: 4, padding: 10,
            }}>
              {PALETTES[activePalette]?.symbols.map((sym, i) => (
                <button
                  key={`${sym}-${i}`}
                  onClick={() => insertSymbol(sym)}
                  title={sym}
                  style={{
                    background: '#0d0d14', border: `1px solid ${border}`,
                    borderRadius: 6, padding: '8px 0', cursor: 'pointer',
                    fontSize: 20, fontFamily: '"Cambria Math", "STIX Two Math", serif',
                    color: '#e2e8f0', transition: 'all 0.12s',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    minHeight: 44,
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = `${accent}22`
                    e.currentTarget.style.borderColor = accent
                    e.currentTarget.style.transform = 'scale(1.1)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = '#0d0d14'
                    e.currentTarget.style.borderColor = border
                    e.currentTarget.style.transform = 'scale(1)'
                  }}
                >
                  {sym}
                </button>
              ))}
            </div>
          </div>

          {/* ─── Templates panel (collapsible) ─── */}
          {showTemplates && (
            <div style={{
              background: card, border: `1px solid ${border}`, borderRadius: 12,
              padding: 12, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
              gap: 6,
            }}>
              {TEMPLATES.map((t, i) => (
                <button
                  key={i}
                  onClick={() => loadTemplate(t.formula)}
                  style={{
                    background: '#0d0d14', border: `1px solid ${border}`,
                    borderRadius: 8, padding: '8px 12px', cursor: 'pointer',
                    textAlign: 'left', transition: 'all 0.12s',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = accent
                    e.currentTarget.style.background = `${accent}11`
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = border
                    e.currentTarget.style.background = '#0d0d14'
                  }}
                >
                  <div style={{ fontSize: 11, color: muted, fontFamily: 'monospace', marginBottom: 4 }}>
                    {t.label}
                  </div>
                  <div style={{ fontSize: 16, fontFamily: '"Cambria Math", serif', color: '#e2e8f0' }}>
                    {t.formula}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ─── Sidebar: History ─── */}
        <div style={{
          width: 260, borderLeft: `1px solid ${border}`, background: card,
          display: 'flex', flexDirection: 'column', flexShrink: 0,
        }}>
          <div style={{
            padding: '12px 16px', borderBottom: `1px solid ${border}`,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <span style={{ fontSize: 12, color: muted, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 1 }}>
              History
            </span>
            {history.length > 0 && (
              <button
                onClick={() => saveHistory([])}
                style={{
                  background: 'transparent', border: 'none',
                  color: muted, fontSize: 11, cursor: 'pointer', fontFamily: 'monospace',
                }}
              >
                clear
              </button>
            )}
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {history.length === 0 ? (
              <div style={{ padding: 16, color: '#334155', fontSize: 12, fontFamily: 'monospace', textAlign: 'center' }}>
                Formulas you build will appear here
              </div>
            ) : (
              history.map((h, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setFormula(h)
                    inputRef.current?.focus()
                  }}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left',
                    background: 'transparent', border: `1px solid transparent`,
                    borderRadius: 6, padding: '8px 10px', cursor: 'pointer',
                    fontSize: 14, fontFamily: '"Cambria Math", serif',
                    color: '#94a3b8', transition: 'all 0.12s',
                    marginBottom: 2, wordBreak: 'break-word',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = border
                    e.currentTarget.style.background = `${accent}11`
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'transparent'
                    e.currentTarget.style.background = 'transparent'
                  }}
                >
                  {h}
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
