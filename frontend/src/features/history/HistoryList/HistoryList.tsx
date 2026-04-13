import type { HistoryEntry } from '@/hooks/useResearchHistory'

import { HistoryItem } from '../HistoryItem/HistoryItem'
import styles from './HistoryList.module.css'

interface HistoryListProps {
  entries: HistoryEntry[]
  onSelect: (entry: HistoryEntry) => void
  onDelete: (id: string) => void
  onClearAll: () => void
}

export function HistoryList({ entries, onSelect, onDelete, onClearAll }: HistoryListProps) {
  if (!entries.length) {
    return (
      <div className={styles.empty}>
        <p className={styles.emptyText}>No research history yet.</p>
        <p className={styles.emptyHint}>Your analyses will appear here.</p>
      </div>
    )
  }

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>Recent Research</h3>
        <button className={styles.clearBtn} onClick={onClearAll}>
          Clear all
        </button>
      </div>
      <div className={styles.list}>
        {entries.map((entry) => (
          <HistoryItem
            key={entry.id}
            entry={entry}
            onClick={onSelect}
            onDelete={onDelete}
          />
        ))}
      </div>
    </section>
  )
}
