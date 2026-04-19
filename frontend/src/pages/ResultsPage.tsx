import { useEffect, useRef } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'

import { TopBar } from '@/components/layout/TopBar/TopBar'
import {
  AnswerPanel,
  SourcesSidebar,
  StatusBar,
  KeywordChips,
  FollowUpBar,
  ErrorBanner,
} from '@/features/results'
import { useChatStream } from '@/hooks/streaming/useChatStream'
import { useAbbreviationBank } from '@/hooks/useAbbreviationBank'
import { useConversation } from '@/hooks/useConversation'
import { useResearchHistory } from '@/hooks/useResearchHistory'
import { generateSessionId } from '@/utils/citations'
import { ROUTES } from '@/router/routes'

import styles from './ResultsPage.module.css'

interface LocationState {
  query?: string
}

export default function ResultsPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const location = useLocation()
  const navigate = useNavigate()

  const { state: streamState, answerText, startStream, reset } = useChatStream()
  const { conversationHistory, addTurn, clearHistory, isFollowUp } = useConversation()
  const { addEntry } = useResearchHistory()
  const { setBank, clearBank } = useAbbreviationBank()

  // The query comes from navigation state (set by HomePage or Sidebar history click).
  // conversationHistory is also passed via state on follow-up navigations.
  const locationState = location.state as LocationState & {
    conversationHistory?: import('@/api/types/api.types').ConversationHistory
  }
  const initialQuery = locationState?.query ?? ''
  const initialHistory = locationState?.conversationHistory
  const currentQueryRef = useRef(initialQuery)

  // ── Start stream on mount / when sessionId changes ─────────────────────────
  useEffect(() => {
    if (!initialQuery) {
      navigate(ROUTES.home, { replace: true })
      return
    }

    clearBank()
    currentQueryRef.current = initialQuery
    reset()
    clearHistory()
    // Pass conversation history from navigation state so follow-ups have context
    startStream(initialQuery, initialHistory)
    return () => {
      clearBank()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  // ── Save to history when stream completes ──────────────────────────────────
  useEffect(() => {
    if (streamState.status !== 'done') return
    if (!currentQueryRef.current || !answerText) return

    setBank(streamState.abbreviationBank)

    addEntry({
      id: sessionId ?? generateSessionId(),
      query: currentQueryRef.current,
      answerPreview: answerText.slice(0, 200),
      papers: streamState.completePapers,
      timestamp: Date.now(),
    })
  }, [
    answerText,
    addEntry,
    sessionId,
    setBank,
    streamState.abbreviationBank,
    streamState.completePapers,
    streamState.status,
  ])

  // ── Follow-up handler ──────────────────────────────────────────────────────
  const handleFollowUp = (followUpQuery: string) => {
    // Append the completed exchange to the thread before navigating
    addTurn({ query: currentQueryRef.current, answer: answerText })

    const newSessionId = generateSessionId()
    currentQueryRef.current = followUpQuery

    // Pass updated conversation history through navigation state so the next
    // ResultsPage mount can include it in the streaming request
    const updatedHistory = {
      messages: [
        ...(conversationHistory?.messages ?? []),
        { role: 'user' as const, content: currentQueryRef.current },
        { role: 'assistant' as const, content: answerText },
      ],
    }

    navigate(ROUTES.results(newSessionId), {
      state: { query: followUpQuery, conversationHistory: updatedHistory },
      replace: false,
    })
  }

  const isStreaming = streamState.status === 'streaming' || streamState.status === 'connecting'

  return (
    <>
      <TopBar currentQuery={currentQueryRef.current} />

      <div className={styles.layout}>
        {/* ── Main answer panel ── */}
        <div className={styles.main}>
          <StatusBar status={streamState.status} />

          <h1 className={styles.query}>{currentQueryRef.current}</h1>

          {isFollowUp && (
            <span className={styles.followUpBadge}>Follow-up question</span>
          )}

          <KeywordChips keywords={streamState.keywords} />

          {streamState.error && <ErrorBanner message={streamState.error} />}

          <AnswerPanel answerText={answerText} status={streamState.status} />

          {/* Show follow-up bar once we have some answer content */}
          {(streamState.status === 'done' || answerText) && (
            <FollowUpBar onSubmit={handleFollowUp} disabled={isStreaming} />
          )}
        </div>

        {/* ── Sources sidebar ── */}
        <SourcesSidebar
          previews={streamState.paperPreviews}
          completePapers={streamState.completePapers}
          keywords={streamState.keywords}
          status={streamState.status}
        />
      </div>
    </>
  )
}
