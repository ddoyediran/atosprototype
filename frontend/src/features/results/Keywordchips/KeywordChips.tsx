import styles from './KeywordChips.module.css'

interface KeywordChipsProps {
  keywords: string[]
}

export function KeywordChips({ keywords }: KeywordChipsProps) {
  if (!keywords.length) return null

  return (
    <div className={styles.row} role="list" aria-label="Search keywords">
      {keywords.map((k) => (
        <span key={k} className={styles.chip} role="listitem">
          {k}
        </span>
      ))}
    </div>
  )
}
