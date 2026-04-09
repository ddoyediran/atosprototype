import { apiFetch, openSSEStream } from '../client'
import type { SSEStreamOptions } from '../client'
import type { QueryRequest, QueryResponse, HealthCheckResponse } from '../types/api.types'

class ChatService {
  /**
   * Non-streaming chat — returns the full response at once.
   * Useful for testing or simple clients.
   */
  async query(request: QueryRequest): Promise<QueryResponse> {
    return apiFetch<QueryResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Streaming chat via SSE.
   * Delegates stream lifecycle to the base client's openSSEStream.
   * The caller supplies onEvent / onError / onComplete via SSEStreamOptions.
   */
  async stream(request: QueryRequest, options: SSEStreamOptions): Promise<void> {
    return openSSEStream('/chat/stream', request, options)
  }

  /**
   * Health check — used on app init to verify the backend is reachable.
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    return apiFetch<HealthCheckResponse>('/health')
  }
}

// Export a single shared instance — no need to instantiate in every hook
export const chatService = new ChatService()