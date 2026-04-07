import { useRef, useCallback } from 'react'

import { chatService } from '@/api/services/chat.service'
import type { QueryRequest } from '@/api/types/api.types'
import type { SSEStreamOptions } from '@/api/client'

/**
 * Manages the raw SSE connection lifecycle.
 * Exposes `connect` and `abort` — does not own any streaming state.
 * State is owned by the parent useChatStream hook via the callbacks.
 */
export function useSSEConnection() {
  const abortControllerRef = useRef<AbortController | null>(null)

  const abort = useCallback(() => {
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
  }, [])

  const connect = useCallback(
    (request: QueryRequest, options: Omit<SSEStreamOptions, 'signal'>) => {
      // Cancel any in-flight stream before starting a new one
      abort()

      const controller = new AbortController()
      abortControllerRef.current = controller

      // Fire and forget — the hook caller handles state via callbacks
      chatService.stream(request, { ...options, signal: controller.signal })
    },
    [abort]
  )

  return { connect, abort }
}