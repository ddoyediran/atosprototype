// ─── Request types ──────────────────────────────────────────────────────────

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp?: string
}

export interface ConversationHistory {
  messages: Message[]
}

export interface QueryRequest {
  query: string
  conversation_history?: ConversationHistory
  force_new_search?: boolean
}

// ─── Response types ──────────────────────────────────────────────────────────

export interface Paper {
  pmid: string
  pmc_id: string | null
  title: string
  authors: string[]
  journal: string | null
  year: number | null
  abstract: string | null
  full_text: string | null
  doi: string | null
  url: string | null
  abbreviations: Record<string, string>
}

export interface Citation {
  index: number
  pmid: string
}

export interface QueryResponse {
  query: string
  answer: string
  papers: Paper[]
  citations: Citation[]
  is_follow_up: boolean
  papers_reused: boolean
  processing_time_ms: number | null
}

export interface HealthCheckResponse {
  status: string
  version: string
  timestamp: string
}

// ─── SSE event types (discriminated union) ───────────────────────────────────
// Each event maps to a backend _sse_event() call in routes.py

export interface SSEKeywordsEvent {
  type: 'keywords'
  data: { keywords: string[] }
}

export interface SSEPapersEvent {
  type: 'papers'
  data: {
    count: number
    papers: Pick<Paper, 'pmid' | 'title' | 'authors' | 'year'>[]
  }
}

export interface SSEAnswerEvent {
  type: 'answer'
  data: { chunk: string }
}

export interface SSECompleteEvent {
  type: 'complete'
  data: {
    papers: Array<
      Pick<Paper, 'pmid' | 'pmc_id' | 'title' | 'authors' | 'journal' | 'year' | 'abstract' | 'doi' | 'url'> & {
        citation: string
      }
    >
  }
}

export interface SSEErrorEvent {
  type: 'error'
  data: { error: string }
}

export interface SSEDoneEvent {
  type: 'done'
  data: Record<string, never>
}

export type SSEEvent =
  | SSEKeywordsEvent
  | SSEPapersEvent
  | SSEAnswerEvent
  | SSECompleteEvent
  | SSEErrorEvent
  | SSEDoneEvent

// ─── Convenience types ────────────────────────────────────────────────────────

/** Paper shape returned in the SSE `complete` event */
export type CompletePaper = SSECompleteEvent['data']['papers'][number]

/** Paper preview shape from SSE `papers` event */
export type PaperPreview = SSEPapersEvent['data']['papers'][number]

/** API error shape returned by FastAPI's HTTPException */
export interface APIError {
  detail: string
}
