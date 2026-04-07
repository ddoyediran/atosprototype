import { useState, useCallback } from 'react'

import type { ConversationHistory, Message } from '@/api/types/api.types'

export interface ConversationTurn {
  query: string
  answer: string
}

export interface UseConversationReturn {
  conversationHistory: ConversationHistory | undefined
  /** Append a completed exchange (user query + assistant answer) to history */
  addTurn: (turn: ConversationTurn) => void
  /** Clear the thread — called when starting a new analysis */
  clearHistory: () => void
  isFollowUp: boolean
}

export function useConversation(): UseConversationReturn {
  const [messages, setMessages] = useState<Message[]>([])

  const addTurn = useCallback(({ query, answer }: ConversationTurn) => {
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: query },
      { role: 'assistant', content: answer },
    ])
  }, [])

  const clearHistory = useCallback(() => {
    setMessages([])
  }, [])

  return {
    conversationHistory: messages.length > 0 ? { messages } : undefined,
    addTurn,
    clearHistory,
    isFollowUp: messages.length > 0,
  }
}