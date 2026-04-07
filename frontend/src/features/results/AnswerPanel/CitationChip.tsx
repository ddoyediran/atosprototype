import styles from './CitationChip.module.css'

interface CitationChipProps {
  number: string
}

/**
 * Inline citation marker rendered from the markdown answer.
 * Styled as a superscript "jewel" per DESIGN.md.
 */
export function CitationChip({ number }: CitationChipProps) {
  return (
    <sup className={styles.chip} data-citation={number} title={`Reference ${number}`}>
      [{number}]
    </sup>
  )
}