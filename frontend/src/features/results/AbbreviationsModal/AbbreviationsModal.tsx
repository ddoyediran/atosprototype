import { useEffect, useMemo } from 'react'

import { Icon } from '@/components/ui/Icon/Icon'
import { useAbbreviationBank } from '@/hooks/useAbbreviationBank'

import styles from './AbbreviationsModal.module.css'

interface AbbreviationRow {
  number: number
  abbreviation: string
  meaning: string
  papers: Array<{
    paper_index: number
    paper_title: string
  }>
}

export function AbbreviationsModal() {
  const { bank, isOpen, close } = useAbbreviationBank()

  const rows = useMemo<AbbreviationRow[]>(() => {
    const unsorted = Object.entries(bank)
      .flatMap(([abbreviation, meanings]) =>
        meanings.map((meaning) => ({
          abbreviation,
          meaning: meaning.full_form,
          papers: [...meaning.papers].sort((left, right) => left.paper_index - right.paper_index),
        }))
      )
      .sort((left, right) => {
        const abbreviationOrder = left.abbreviation.localeCompare(right.abbreviation)
        if (abbreviationOrder !== 0) return abbreviationOrder
        return left.meaning.localeCompare(right.meaning)
      })
    return unsorted.map((row, index) => ({ ...row, number: index + 1 }))
  }, [bank])

  const abbreviationCount = Object.keys(bank).length
  const meaningCount = rows.length

  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        close()
      }
    }

    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.body.style.overflow = ''
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [close, isOpen])

  if (!isOpen) {
    return null
  }

  return (
    <div
      className={styles.backdrop}
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          close()
        }
      }}
    >
      <section
        className={styles.panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="abbreviations-title"
        aria-describedby="abbreviations-description"
      >
        <header className={styles.header}>
          <div>
            <span className={styles.eyebrow}>Abbreviations</span>
            <h2 id="abbreviations-title" className={styles.title}>
              Abbreviation bank
            </h2>
            <p id="abbreviations-description" className={styles.subtitle}>
              Meanings extracted from the current paper set, grouped with the indexed papers that use each meaning.
            </p>
          </div>

          <button className={styles.closeBtn} type="button" onClick={close} aria-label="Close abbreviations modal">
            <Icon name="close" size={18} />
          </button>
        </header>

        <div className={styles.body}>
          <div className={styles.summary}>
            <span className={styles.summaryBadge}>{abbreviationCount} abbreviations</span>
            <span>{meaningCount} meanings</span>
          </div>

          {rows.length === 0 ? (
            <div className={styles.empty}>
              No abbreviations were extracted for this analysis yet.
            </div>
          ) : (
            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Abbreviation</th>
                    <th>Meaning</th>
                    <th>Paper indexes</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={`${row.abbreviation}-${row.meaning}`}>
                      <td className={styles.numberCell}>{row.number}</td>
                      <td className={styles.abbrCell}>{row.abbreviation}</td>
                      <td className={styles.meaningCell}>{row.meaning}</td>
                      <td className={styles.papersCell}>
                        <div className={styles.paperList}>
                          {row.papers.map((paper) => (
                            <span
                              key={`${row.abbreviation}-${row.meaning}-${paper.paper_index}`}
                              className={styles.paperChip}
                              title={paper.paper_title}
                            >
                              {paper.paper_index}
                            </span>
                          ))}
                        </div>
                        {row.papers.length > 0 &&
                          row.papers.map((paper) => (
                            <span key={`${paper.paper_index}-title`} className={styles.paperTitle}>
                              {paper.paper_index}: {paper.paper_title}
                            </span>
                          ))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}