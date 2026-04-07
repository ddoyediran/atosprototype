import styles from './SuggestionChips.module.css'

const DEFAULT_SUGGESTIONS = [
  'CRISPR breakthroughs 2024',
  'Long COVID meta-analysis',
  'Rare disease biomarkers',
]

interface SuggestionChipsProps {
  suggestions?: string[]
  onSelect: (suggestion: string) => void
}

export function SuggestionChips({
  suggestions = DEFAULT_SUGGESTIONS,
  onSelect,
}: SuggestionChipsProps) {
  return (
    <div className={styles.row}>
      <span className={styles.label}>Try searching:</span>
      {suggestions.map((s) => (
        <button key={s} className={styles.chip} onClick={() => onSelect(s)}>
          {s}
        </button>
      ))}
    </div>
  )
}