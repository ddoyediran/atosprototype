import { useState, type KeyboardEvent } from 'react'

import { Icon } from '@/components/ui/Icon/Icon'

import styles from './FollowUpBar.module.css'

interface FollowUpBarProps {
  onSubmit: (query: string) => void
  disabled?: boolean
}

export function FollowUpBar({ onSubmit, disabled = false }: FollowUpBarProps) {
  const [value, setValue] = useState('')

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit()
  }

  return (
    <div className={styles.bar}>
      <input
        className={styles.input}
        placeholder="Ask a follow-up question… (e.g., 'What are the long-term side effects?')"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        aria-label="Follow-up question"
      />
      <button
        className={styles.sendBtn}
        onClick={handleSubmit}
        disabled={!value.trim() || disabled}
        aria-label="Send follow-up"
      >
        <Icon name="send" size={16} />
      </button>
    </div>
  )
}
