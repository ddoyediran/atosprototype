import { useState } from 'react'

import { Icon } from '@/components/ui/Icon/Icon'
import type { CompletePaper } from '@/api/types/api.types'
import { formatAuthors } from '@/utils/citations'

import styles from './SourceCard.module.css'

interface SourceCardProps {
  paper: CompletePaper
  index: number
}

const ABSTRACT_PREVIEW_LENGTH = 220

export function SourceCard({ paper, index }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false)

  const abstract = paper.abstract ?? ''
  const isLong = abstract.length > ABSTRACT_PREVIEW_LENGTH
  const displayAbstract = isLong && !expanded
    ? abstract.slice(0, ABSTRACT_PREVIEW_LENGTH) + '…'
    : abstract

  const meta = [
    formatAuthors(paper.authors),
    paper.journal,
    paper.year != null ? String(paper.year) : null,
  ]
    .filter(Boolean)
    .join(' · ')

  return (
    <div className={styles.card}>
      <div className={styles.indexBadge}>{index}</div>

      <div className={styles.body}>
        {paper.url ? (
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.title}
          >
            {paper.title}
            <Icon name="externalLink" size={11} className={styles.extIcon} />
          </a>
        ) : (
          <p className={styles.title}>{paper.title}</p>
        )}

        {meta && <p className={styles.meta}>{meta}</p>}

        {paper.citation && (
          <p className={styles.citation}>{paper.citation}</p>
        )}

        {abstract && (
          <div className={styles.abstract}>
            <p className={styles.abstractText}>{displayAbstract}</p>
            {isLong && (
              <button
                className={styles.toggle}
                onClick={() => setExpanded((prev: boolean) => !prev)}
              >
                {expanded ? 'Show less' : 'Show more'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
