import { Spinner } from '@/components/ui/Spinner/Spinner'
import type { StreamStatus } from '@/hooks/streaming/useStreamReducer'

import styles from './StatusBar.module.css'

interface StatusBarProps {
  status: StreamStatus
  processingTime?: number
}

export function StatusBar({ status, processingTime }: StatusBarProps) {
  return (
    <div className={styles.bar}>
      <span className={styles.badge}>QUERY ANALYSIS</span>

      {status === 'connecting' && (
        <span className={styles.info}>
          <Spinner size={12} /> Connecting…
        </span>
      )}

      {status === 'streaming' && (
        <span className={styles.info}>
          <Spinner size={12} /> Searching literature…
        </span>
      )}

      {status === 'done' && (
        <span className={`${styles.info} ${styles.infoSuccess}`}>
          ✓ Analysis complete{processingTime ? ` in ${(processingTime / 1000).toFixed(1)}s` : ''}
        </span>
      )}

      {status === 'error' && (
        <span className={`${styles.info} ${styles.infoError}`}>✗ Error</span>
      )}
    </div>
  )
}
