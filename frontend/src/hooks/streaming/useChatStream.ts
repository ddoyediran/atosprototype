import { useReducer, useCallback, useEffect, useRef } from 'react'

import { useSSEConnection } from './useSSEConnection'
import { streamReducer, INITIAL_STREAM_STATE } from './useStreamReducer'
import type { StreamState } from './useStreamReducer'
import {
  SSEKeywordsDataSchema,
  SSEPapersDataSchema,
  SSEAnswerDataSchema,
  SSECompleteDataSchema,
  SSEErrorDataSchema,
} from '@/api/schemas'
import type { QueryRequest, ConversationHistory } from '@/api/types/api.types'

// ─── Chunk batching ───────────────────────────────────────────────────────────
// SSE can deliver chunks faster than React renders.
// We buffer chunks and flush every BATCH_INTERVAL_MS to avoid 200+ renders
// per response. This is the most impactful performance optimisation here.
const BATCH_INTERVAL_MS = 40

export interface UseChatStreamReturn {
  state: StreamState
  /** Computed: all answer chunks joined into a single string */
  answerText: string
  startStream: (query: string, history?: ConversationHistory) => void
  reset: () => void
}

export function useChatStream(): UseChatStreamReturn {
  const [state, dispatch] = useReducer(streamReducer, INITIAL_STREAM_STATE)
  const { connect, abort } = useSSEConnection()

  // Chunk batching buffer
  const chunkBufferRef = useRef<string[]>([])
  const batchTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const flushChunks = useCallback(() => {
    if (chunkBufferRef.current.length === 0) return
    const combined = chunkBufferRef.current.join('')
    chunkBufferRef.current = []
    dispatch({ type: 'CHUNK', payload: combined })
  }, [])

  const startBatching = useCallback(() => {
    if (batchTimerRef.current) return
    batchTimerRef.current = setInterval(flushChunks, BATCH_INTERVAL_MS)
  }, [flushChunks])

  const stopBatching = useCallback(() => {
    if (batchTimerRef.current) {
      clearInterval(batchTimerRef.current)
      batchTimerRef.current = null
    }
    // Flush any remaining buffered chunks
    flushChunks()
  }, [flushChunks])

  // Abort + clean up on unmount
  useEffect(() => {
    return () => {
      abort()
      stopBatching()
    }
  }, [abort, stopBatching])

  const startStream = useCallback(
    (query: string, history?: ConversationHistory) => {
      stopBatching()
      chunkBufferRef.current = []
      dispatch({ type: 'RESET' })
      dispatch({ type: 'CONNECT' })

      const request: QueryRequest = {
        query,
        ...(history ? { conversation_history: history } : {}),
      }

      connect(request, {
        onEvent(eventType, data) {
          switch (eventType) {
            case 'keywords': {
              const parsed = SSEKeywordsDataSchema.safeParse(data)
              if (parsed.success) {
                dispatch({ type: 'KEYWORDS', payload: parsed.data.keywords })
                startBatching()
              }
              break
            }
            case 'papers': {
              const parsed = SSEPapersDataSchema.safeParse(data)
              if (parsed.success) {
                dispatch({ type: 'PAPERS', payload: parsed.data.papers })
              }
              break
            }
            case 'answer': {
              const parsed = SSEAnswerDataSchema.safeParse(data)
              if (parsed.success) {
                // Buffer the chunk — the interval timer will flush it
                chunkBufferRef.current.push(parsed.data.chunk)
              }
              break
            }
            case 'complete': {
              stopBatching()
              const parsed = SSECompleteDataSchema.safeParse(data)
              if (parsed.success) {
                dispatch({
                  type: 'COMPLETE',
                  payload: {
                    papers: parsed.data.papers,
                    abbreviationBank: parsed.data.abbreviation_bank,
                  },
                })
              }
              break
            }
            case 'error': {
              stopBatching()
              const parsed = SSEErrorDataSchema.safeParse(data)
              dispatch({
                type: 'ERROR',
                payload: parsed.success ? parsed.data.error : 'An unexpected error occurred',
              })
              break
            }
            case 'done': {
              stopBatching()
              break
            }
          }
        },
        onError(err) {
          stopBatching()
          dispatch({ type: 'ERROR', payload: err.message })
        },
        onComplete() {
          stopBatching()
        },
      })
    },
    [connect, startBatching, stopBatching]
  )

  const reset = useCallback(() => {
    abort()
    stopBatching()
    chunkBufferRef.current = []
    dispatch({ type: 'RESET' })
  }, [abort, stopBatching])

  return {
    state,
    answerText: state.answerChunks.join(''),
    startStream,
    reset,
  }
}