import type { APIError } from './types/api.types'

// ─── Config ───────────────────────────────────────────────────────────────────

const API_BASE = import.meta.env.VITE_API_BASE as string

if (!API_BASE) {
  throw new Error('VITE_API_BASE environment variable is not set. Check your .env file.')
}

// ─── Error types ──────────────────────────────────────────────────────────────

export class APIClientError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly detail?: string
  ) {
    super(message)
    this.name = 'APIClientError'
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'NetworkError'
  }
}

// ─── Base fetch helper ────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${path}`

  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      headers: { ...defaultHeaders, ...options.headers },
    })
  } catch (err) {
    // Network-level failure (no connection, DNS, CORS preflight)
    throw new NetworkError(
      err instanceof Error ? err.message : 'Network request failed'
    )
  }

  if (!response.ok) {
    let detail: string | undefined
    try {
      const body = (await response.json()) as APIError
      detail = body.detail
    } catch {
      // Body is not JSON — use status text
    }
    throw new APIClientError(
      `API error ${response.status}: ${detail ?? response.statusText}`,
      response.status,
      detail
    )
  }

  return response.json() as Promise<T>
}

// ─── SSE stream helper ────────────────────────────────────────────────────────

export interface SSEStreamOptions {
  signal: AbortSignal
  onEvent: (eventType: string, data: unknown) => void
  onError: (err: Error) => void
  onComplete: () => void
}

/**
 * Opens an SSE stream to `path` with a POST body.
 * Parses `event:` / `data:` pairs and calls `onEvent` for each.
 *
 * The caller is responsible for providing an AbortSignal so the stream
 * can be cancelled on unmount or new query.
 */
export async function openSSEStream(
  path: string,
  body: unknown,
  options: SSEStreamOptions
): Promise<void> {
  const url = `${API_BASE}${path}`
  const { signal, onEvent, onError, onComplete } = options

  let response: Response
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(body),
      signal,
    })
  } catch (err) {
    if ((err as Error).name === 'AbortError') return
    onError(new NetworkError(err instanceof Error ? err.message : 'Stream connection failed'))
    return
  }

  if (!response.ok || !response.body) {
    let detail: string | undefined
    try {
      const b = (await response.json()) as APIError
      detail = b.detail
    } catch {
      /* ignore */
    }
    onError(new APIClientError(`Stream error ${response.status}`, response.status, detail))
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE blocks are separated by double newline
      const blocks = buffer.split('\n\n')
      buffer = blocks.pop() ?? ''

      for (const block of blocks) {
        if (!block.trim()) continue

        let eventType = 'message'
        let dataStr = ''

        for (const line of block.split('\n')) {
          if (line.startsWith('event:')) eventType = line.slice(6).trim()
          if (line.startsWith('data:')) dataStr = line.slice(5).trim()
        }

        if (!dataStr) continue

        let parsed: unknown
        try {
          parsed = JSON.parse(dataStr)
        } catch {
          continue // Malformed data line — skip silently
        }

        onEvent(eventType, parsed)
      }
    }
  } catch (err) {
    if ((err as Error).name !== 'AbortError') {
      onError(err instanceof Error ? err : new Error('Stream read error'))
    }
  } finally {
    reader.releaseLock()
    onComplete()
  }
}

export { apiFetch }