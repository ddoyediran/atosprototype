import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { CompletePaper } from '@/api/types/api.types'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface HistoryEntry {
  id: string
  query: string
  answerPreview: string   // First 200 chars of the answer
  papers: CompletePaper[]
  timestamp: number
}

interface HistoryStore {
  entries: HistoryEntry[]
  addEntry: (entry: HistoryEntry) => void
  removeEntry: (id: string) => void
  clearAll: () => void
}

// ─── Store ────────────────────────────────────────────────────────────────────
// Zustand's `persist` middleware handles localStorage automatically.
// No manual load/save logic needed anywhere in the app.

const MAX_HISTORY_ENTRIES = 25

export const useHistoryStore = create<HistoryStore>()(
  persist(
    (set) => ({
      entries: [],

      addEntry: (entry) =>
        set((state) => {
          // Deduplicate by query (case-insensitive) — update timestamp if same query
          const filtered = state.entries.filter(
            (e) => e.query.toLowerCase() !== entry.query.toLowerCase()
          )
          return {
            entries: [entry, ...filtered].slice(0, MAX_HISTORY_ENTRIES),
          }
        }),

      removeEntry: (id) =>
        set((state) => ({
          entries: state.entries.filter((e) => e.id !== id),
        })),

      clearAll: () => set({ entries: [] }),
    }),
    {
      name: 'capmed-research-history', // localStorage key
    }
  )
)

// ─── Convenience hook ─────────────────────────────────────────────────────────
// Components use this, not useHistoryStore directly, to avoid coupling them
// to the Zustand store shape.

export function useResearchHistory() {
  const { entries, addEntry, removeEntry, clearAll } = useHistoryStore()
  return { entries, addEntry, removeEntry, clearAll }
}