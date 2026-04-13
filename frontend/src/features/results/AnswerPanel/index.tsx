import { useEffect, useRef, memo } from 'react'

import { SkeletonParagraph } from '@/components/ui/Skeleton/Skeleton'
import { renderMarkdown } from '@/utils/markdown'
import type { StreamStatus } from '@/hooks/streaming/useStreamReducer'

import styles from './AnswerPanel.module.css'

interface AnswerPanelProps {
  answerText: string
  status: StreamStatus
}

export const AnswerPanel = memo(function AnswerPanel({ answerText, status }: AnswerPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom as answer streams in
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [answerText])

  if (status === 'connecting' && !answerText) {
    return (
      <div className={styles.skeleton}>
        <SkeletonParagraph lines={5} />
      </div>
    )
  }

  if (!answerText) return null

  return (
    <div className={styles.panel}>
      <div
        className={styles.prose}
        // Safe: source is always the backend LLM response, never raw user input
        dangerouslySetInnerHTML={{ __html: renderMarkdown(answerText) }}
      />
      {status === 'streaming' && <span className={styles.cursor}>▍</span>}
      <div ref={bottomRef} />
    </div>
  )
})
