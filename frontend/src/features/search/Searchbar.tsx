import {
  useState,
  useRef,
  forwardRef,
  useImperativeHandle,
  type KeyboardEvent,
} from 'react'

import { Icon } from '@/components/ui/Icon/Icon'

import styles from './SearchBar.module.css'

// ─── Public handle ─────────────────────────────────────────────────────────────
// Exposed via ref so HomePage can fill the input when a suggestion chip is
// clicked, without lifting all query state to the page level.

export interface SearchBarHandle {
  fill: (text: string) => void
  focus: () => void
}

interface SearchBarProps {
  onSubmit: (query: string) => void
  initialValue?: string
  placeholder?: string
}

export const SearchBar = forwardRef<SearchBarHandle, SearchBarProps>(
  function SearchBar(
    {
      onSubmit,
      initialValue = '',
      placeholder = 'What is the current consensus on GLP-1 for cardiovascular risk?',
    },
    ref
  ) {
    const [value, setValue] = useState(initialValue)
    const inputRef = useRef<HTMLInputElement>(null)

    useImperativeHandle(ref, () => ({
      fill: (text: string) => {
        setValue(text)
        inputRef.current?.focus()
      },
      focus: () => inputRef.current?.focus(),
    }))

    const handleSubmit = () => {
      const trimmed = value.trim()
      if (!trimmed) return
      onSubmit(trimmed)
    }

    const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') handleSubmit()
    }

    return (
      <div className={styles.bar}>
        <Icon name="search" size={22} className={styles.searchIcon} />
        <input
          ref={inputRef}
          className={styles.input}
          placeholder={placeholder}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          autoFocus
          aria-label="Research query"
        />
        <button
          className={styles.askBtn}
          onClick={handleSubmit}
          disabled={!value.trim()}
          aria-label="Submit query"
        >
          Ask
          <Icon name="arrowRight" size={14} />
        </button>
      </div>
    )
  }
)