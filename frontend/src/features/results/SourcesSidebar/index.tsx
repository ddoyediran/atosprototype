import { SkeletonParagraph } from '@/components/ui/Skeleton/Skeleton'
import type { PaperPreview, CompletePaper } from '@/api/types/api.types'
import type { StreamStatus } from '@/hooks/streaming/useStreamReducer'

import { SourceCard } from './SourceCard'
import styles from './SourcesSidebar.module.css'

interface SourcesSidebarProps {
  previews: PaperPreview[]
  completePapers: CompletePaper[]
  keywords: string[]
  status: StreamStatus
}

export function SourcesSidebar({ previews, completePapers, status }: SourcesSidebarProps) {
  const isConnecting = status === 'connecting'
  const hasFull = completePapers.length > 0
  const count = hasFull ? completePapers.length : previews.length

  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <span className={styles.title}>Sources</span>
        {count > 0 && <span className={styles.badge}>{count}</span>}
      </div>

      {/* Loading skeleton */}
      {isConnecting && (
        <div className={styles.skeletonList}>
          <SkeletonParagraph lines={4} />
          <SkeletonParagraph lines={4} />
          <SkeletonParagraph lines={3} />
        </div>
      )}

      {/* Full paper cards once stream completes */}
      {!isConnecting && hasFull && (
        <div className={styles.list}>
          {completePapers.map((paper, idx) => (
            <SourceCard key={paper.pmid} paper={paper} index={idx + 1} />
          ))}
        </div>
      )}

      {/* Preview cards while streaming (title + authors only) */}
      {!isConnecting && !hasFull && previews.length > 0 && (
        <div className={styles.list}>
          {previews.map((preview, idx) => (
            <div key={preview.pmid} className={styles.preview}>
              <span className={styles.previewNum}>{idx + 1}</span>
              <div className={styles.previewContent}>
                <p className={styles.previewTitle}>{preview.title}</p>
                <p className={styles.previewMeta}>
                  {preview.authors[0]
                    ? `${preview.authors[0]}${preview.authors.length > 1 ? ' et al.' : ''}`
                    : 'Unknown authors'}
                  {preview.year != null ? ` · ${preview.year}` : ''}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isConnecting && count === 0 && status !== 'idle' && (
        <p className={styles.empty}>No sources found.</p>
      )}
    </aside>
  )
}
