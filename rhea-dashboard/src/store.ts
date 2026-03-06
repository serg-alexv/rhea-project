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
}

export const useStore = create<Store>((set) => ({
  sessions: [],
  procs: [
    { name: 'Session Server', port: 3000, status: 'running', uptime: 3600 },
    { name: 'AI Auth', port: 3001, status: 'running', uptime: 3600 },
    { name: 'Angel Game', port: 3002, status: 'running', uptime: 3600 },
    { name: 'BioRenderer', port: 3003, status: 'running', uptime: 3600 },
    { name: 'RAG Storage', port: 3004, status: 'running', uptime: 3600 },
  ],
  
  fetchSessions: async () => {
    try {
      const res = await axios.get('/api/sessions')
      set({ sessions: res.data.sessions || [] })
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
    }
  },
  
  fetchProcs: async () => {
    // Mock: procs are static for now
  }
}))
