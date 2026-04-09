import { Icon } from '@/components/ui/Icon/Icon'
import type { HistoryEntry } from '@/hooks/useResearchHistory'

import styles from '../HistoryList/HistoryList.module.css'

interface HistoryItemProps {
  entry: HistoryEntry
  onClick: (entry: HistoryEntry) => void
  onDelete: (id: string) => void
}

export function HistoryItem({ entry, onClick, onDelete }: HistoryItemProps) {
  const date = new Date(entry.timestamp).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })

  return (
    <div className={styles.item}>
      <button className={styles.itemBody} onClick={() => onClick(entry)}>
        <Icon name="history" size={14} className={styles.itemIcon} />
        <div className={styles.itemContent}>
          <span className={styles.itemQuery}>
            {entry.query.length > 60 ? entry.query.slice(0, 60) + '…' : entry.query}
          </span>
          <span className={styles.itemMeta}>
            {date} · {entry.papers.length} sources
          </span>
        </div>
      </button>
      <button
        className={styles.deleteBtn}
        onClick={() => onDelete(entry.id)}
        aria-label="Remove from history"
        title="Remove"
      >
        <Icon name="close" size={12} />
      </button>
    </div>
  )
}
