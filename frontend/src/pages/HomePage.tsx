import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import { TopBar } from '@/components/layout/TopBar/TopBar'
import { SearchBar } from '@/features/search'
import type { SearchBarHandle } from '@/features/search'
import { SuggestionChips } from '@/features/search'
import { QuickAskGrid } from '@/features/search'
import { HistoryList } from '@/features/history'
import { useResearchHistory } from '@/hooks/useResearchHistory'
import { generateSessionId } from '@/utils/citations'
import { ROUTES } from '@/router/routes'

import styles from './HomePage.module.css'

export default function HomePage() {
  const navigate = useNavigate()
  const { entries, removeEntry, clearAll } = useResearchHistory()
  const searchBarRef = useRef<SearchBarHandle>(null)

  const handleQuery = (query: string) => {
    const sessionId = generateSessionId()
    navigate(ROUTES.results(sessionId), { state: { query } })
  }

  // Suggestion chips fill the search bar rather than submitting immediately —
  // lets the user review / modify the query before hitting Ask
  const handleSuggestionSelect = (suggestion: string) => {
    searchBarRef.current?.fill(suggestion)
  }

  const handleHistorySelect = (entry: { query: string; id: string }) => {
    navigate(ROUTES.results(entry.id), { state: { query: entry.query } })
  }

  return (
    <>
      <TopBar />
      <main className={styles.main}>
        {/* Hero search */}
        <section className={styles.hero}>
          <h2 className={styles.tagline}>
            Evidence-based answers from<br />
            <span className={styles.taglineAccent}>peer-reviewed research.</span>
          </h2>

          <SearchBar ref={searchBarRef} onSubmit={handleQuery} />
          <SuggestionChips onSelect={handleSuggestionSelect} />
        </section>

        {/* Quick Ask grid — submits immediately */}
        <QuickAskGrid onSelect={handleQuery} />

        {/* Research history */}
        <HistoryList
          entries={entries}
          onSelect={handleHistorySelect}
          onDelete={removeEntry}
          onClearAll={clearAll}
        />
      </main>
    </>
  )
}
