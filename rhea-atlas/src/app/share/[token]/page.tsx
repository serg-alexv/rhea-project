'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

const API = process.env.NEXT_PUBLIC_CC_API ?? 'http://localhost:8400'

const bg = '#0a0a0f'
const card = '#111118'
const border = '#1e1e2e'
const accent = '#6366f1'
const green = '#22c55e'
const muted = '#64748b'

interface ShareData {
  token: string
  content_type: string
  title: string
  content: string
  views: number
  created_at: string
  expires_at: string | null
  metadata?: Record<string, unknown>
}

export default function SharePage() {
  const params = useParams()
  const token = params?.token as string
  const [data, setData] = useState<ShareData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!token) return
    fetch(`${API}/share/${token}`)
      .then(r => {
        if (!r.ok) throw new Error(r.status === 404 ? 'Share not found or expired' : `HTTP ${r.status}`)
        return r.json()
      })
      .then(setData)
      .catch(e => setError(e.message))
  }, [token])

  const copyContent = () => {
    if (!data) return
    navigator.clipboard.writeText(data.content).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  const typeLabel = (t: string) => {
    const map: Record<string, string> = {
      formula: 'Logical Formula',
      proof: 'Verified Proof',
      graphic: 'Graphic',
      text: 'Text',
      session: 'Session Transcript',
    }
    return map[t] || t
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', background: bg, color: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>404</div>
          <div style={{ color: muted, marginBottom: 24 }}>{error}</div>
          <Link href="/" style={{ color: accent, textDecoration: 'none', fontSize: 14 }}>Back to Rhea</Link>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div style={{ minHeight: '100vh', background: bg, color: muted, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        Loading...
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: bg, color: '#e2e8f0', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* Header */}
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 24px', borderBottom: `1px solid ${border}` }}>
        <Link href="/" style={{ color: accent, textDecoration: 'none', fontSize: 14, fontFamily: 'monospace', fontWeight: 700 }}>
          rhea
        </Link>
        <span style={{ color: muted }}>/</span>
        <span style={{ color: muted, fontSize: 13, fontFamily: 'monospace' }}>share</span>
        <div style={{ flex: 1 }} />
        <span style={{
          fontSize: 11, fontFamily: 'monospace', padding: '3px 8px',
          background: `${accent}22`, border: `1px solid ${accent}44`, borderRadius: 4,
          color: accent,
        }}>
          {typeLabel(data.content_type)}
        </span>
      </header>

      {/* Content */}
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 24px' }}>
        {/* Title */}
        {data.title && (
          <h1 style={{ margin: '0 0 16px', fontSize: 24, fontWeight: 700 }}>
            {data.title}
          </h1>
        )}

        {/* Meta */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 24, fontSize: 12, color: muted, fontFamily: 'monospace' }}>
          <span>{new Date(data.created_at).toLocaleDateString()}</span>
          <span>{data.views} view{data.views !== 1 ? 's' : ''}</span>
          {data.expires_at && (
            <span>expires {new Date(data.expires_at).toLocaleDateString()}</span>
          )}
        </div>

        {/* Content card */}
        <div style={{
          background: card, border: `1px solid ${border}`, borderRadius: 12,
          padding: 24, position: 'relative',
        }}>
          {/* Copy button */}
          <button
            onClick={copyContent}
            style={{
              position: 'absolute', top: 12, right: 12,
              background: copied ? `${green}22` : 'transparent',
              border: `1px solid ${copied ? green : border}`,
              color: copied ? green : muted,
              borderRadius: 6, padding: '4px 10px', cursor: 'pointer',
              fontSize: 11, fontFamily: 'monospace',
            }}
          >
            {copied ? 'Copied' : 'Copy'}
          </button>

          {/* Render based on content_type */}
          {data.content_type === 'formula' ? (
            <div style={{
              fontSize: 28, fontFamily: '"Cambria Math", "STIX Two Math", serif',
              letterSpacing: 1.5, lineHeight: 1.8, wordBreak: 'break-word',
            }}>
              {data.content}
            </div>
          ) : data.content_type === 'graphic' ? (
            <div dangerouslySetInnerHTML={{ __html: data.content }} />
          ) : (
            <pre style={{
              margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              fontFamily: '"Fira Code", "SF Mono", monospace', fontSize: 14,
              lineHeight: 1.6, color: '#cbd5e1',
            }}>
              {data.content}
            </pre>
          )}
        </div>

        {/* Footer */}
        <div style={{ marginTop: 32, textAlign: 'center', fontSize: 12, color: muted, fontFamily: 'monospace' }}>
          Shared via <Link href="/" style={{ color: accent, textDecoration: 'none' }}>Rhea</Link>
        </div>
      </div>
    </div>
  )
}
