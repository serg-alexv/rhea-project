import { create } from 'zustand'
import axios from 'axios'

interface Session {
  id: string
  created_at: number
  message_count: number
  lamport_clock: number
  devices: number
}

interface Proc {
  name: string
  port: number
  status: 'running' | 'stopped'
  uptime: number
}

interface Store {
  sessions: Session[]
  procs: Proc[]
  fetchSessions: () => Promise<void>
  fetchProcs: () => Promise<void>
  startPolling: () => void
  stopPolling: () => void
}

let pollInterval: NodeJS.Timeout | null = null

export const useStore = create<Store>((set) => ({
  sessions: [],
  procs: [
    { name: 'Session Server', port: 3000, status: 'running', uptime: 3600 },
    { name: 'AI Auth', port: 3001, status: 'running', uptime: 3600 },
    { name: 'Angel Game', port: 3002, status: 'running', uptime: 3600 },
    { name: 'BioRenderer', port: 3003, status: 'running', uptime: 3600 },
    { name: 'RAG Storage', port: 3004, status: 'running', uptime: 3600 },
    { name: 'Play Token Mapper', port: 3006, status: 'running', uptime: 3600 },
    { name: 'Logical Keyboard', port: 3005, status: 'running', uptime: 3600 },
  ],
  
  fetchSessions: async () => {
    try {
      const res = await axios.get('http://localhost:3000/sessions')
      const sessions = res.data.map((s: any) => ({
        id: s.id,
        created_at: s.created_at,
        message_count: s.message_count,
        lamport_clock: s.lamport_clock,
        devices: s.devices || 1,
      }))
      set({ sessions })
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
    }
  },
  
  fetchProcs: async () => {
    // Procs are static for now
  },

  startPolling: () => {
    if (pollInterval) return
    const { fetchSessions, fetchProcs } = useStore.getState()
    fetchSessions()
    fetchProcs()
    pollInterval = setInterval(() => {
      fetchSessions()
      fetchProcs()
    }, 2000) // Poll every 2 seconds
  },

  stopPolling: () => {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }
}))
