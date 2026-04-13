import styles from './QuickAskGrid.module.css'

const DEFAULT_PROMPTS = [
  'Targeting KRAS G12C in NSCLC',
  'Antibiotic Resistance in S. Aureus',
  'CAR-T Cell Therapy Side Effects',
  'AI in Radiological Diagnosis',
]

interface QuickAskGridProps {
  prompts?: string[]
  onSelect: (prompt: string) => void
}

export function QuickAskGrid({ prompts = DEFAULT_PROMPTS, onSelect }: QuickAskGridProps) {
  return (
    <section className={styles.section}>
      <h3 className={styles.title}>Quick Ask</h3>
      <div className={styles.grid}>
        {prompts.map((prompt, i) => (
          <button
            key={prompt}
            className={`${styles.card} ${i === 0 ? styles.cardActive : ''}`}
            onClick={() => onSelect(prompt)}
          >
            <span className={styles.cardText}>{prompt}</span>
          </button>
        ))}
      </div>
    </section>
  )
}