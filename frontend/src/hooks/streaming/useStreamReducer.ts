import type { AbbreviationBank, CompletePaper, PaperPreview } from '@/api/types/api.types'

// ─── States ───────────────────────────────────────────────────────────────────
// Valid transitions:
//   idle → connecting → streaming → done
//   connecting → error
//   streaming  → error
//   any        → idle  (reset)

export type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'done' | 'error'

export interface StreamState {
  status: StreamStatus
  keywords: string[]
  paperPreviews: PaperPreview[]
  answerChunks: string[]
  completePapers: CompletePaper[]
  abbreviationBank: AbbreviationBank
  error: string | null
}

export const INITIAL_STREAM_STATE: StreamState = {
  status: 'idle',
  keywords: [],
  paperPreviews: [],
  answerChunks: [],
  completePapers: [],
  abbreviationBank: {},
  error: null,
}

// ─── Actions ──────────────────────────────────────────────────────────────────

export type StreamAction =
  | { type: 'CONNECT' }
  | { type: 'KEYWORDS'; payload: string[] }
  | { type: 'PAPERS'; payload: PaperPreview[] }
  | { type: 'CHUNK'; payload: string }
  | { type: 'COMPLETE'; payload: { papers: CompletePaper[]; abbreviationBank: AbbreviationBank } }
  | { type: 'ERROR'; payload: string }
  | { type: 'RESET' }

// ─── Reducer ──────────────────────────────────────────────────────────────────

export function streamReducer(state: StreamState, action: StreamAction): StreamState {
  switch (action.type) {
    case 'CONNECT':
      // Only allow connecting from idle
      if (state.status !== 'idle') return state
      return { ...INITIAL_STREAM_STATE, status: 'connecting' }

    case 'KEYWORDS':
      // Keywords arriving means we are streaming
      return { ...state, status: 'streaming', keywords: action.payload }

    case 'PAPERS':
      return { ...state, paperPreviews: action.payload }

    case 'CHUNK':
      // Append chunk — immutable concat
      return { ...state, answerChunks: [...state.answerChunks, action.payload] }

    case 'COMPLETE':
      return {
        ...state,
        status: 'done',
        completePapers: action.payload.papers,
        abbreviationBank: action.payload.abbreviationBank,
      }

    case 'ERROR':
      return { ...state, status: 'error', error: action.payload }

    case 'RESET':
      return { ...INITIAL_STREAM_STATE }

    default:
      return state
  }
}