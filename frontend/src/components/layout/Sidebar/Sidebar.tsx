import { useNavigate, useLocation } from 'react-router-dom'

import capLogo from '@/assets/cap_logo.svg'
import { Icon } from '@/components/ui/Icon/Icon'
import { AbbreviationsModal } from '@/features/results/AbbreviationsModal/AbbreviationsModal'
import { useAbbreviationBank } from '@/hooks/useAbbreviationBank'
import { useResearchHistory } from '@/hooks/useResearchHistory'
import { ROUTES } from '@/router/routes'

import styles from './Sidebar.module.css'

export function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { entries } = useResearchHistory()
  const { bank, open } = useAbbreviationBank()

  const isHome = location.pathname === ROUTES.home
  const abbreviationCount = Object.keys(bank).length

  return (
    <>
      <aside className={styles.sidebar}>
        {/* Brand */}
        <div className={styles.brand}>
          <div className={styles.logo}>
            <img src={capLogo} alt="CapMed-Sci logo" className={styles.logoImg} />
          </div>
          <div>
            <p className={styles.appName}>CapMed-Sci</p>
            <p className={styles.appSub}>Medical Research Suite</p>
          </div>
        </div>

        {/* New Analysis CTA */}
        <button className={styles.newBtn} onClick={() => navigate(ROUTES.home)}>
          <Icon name="plus" size={16} />
          New Analysis
        </button>

        {/* Nav */}
        <nav className={styles.nav}>
          <button
            className={`${styles.navItem} ${isHome ? styles.navItemActive : ''}`}
            onClick={() => navigate(ROUTES.home)}
          >
            <Icon name="history" size={16} />
            Research History
          </button>
        </nav>

        {/* History entries */}
        {entries.length > 0 && (
          <div className={styles.history}>
            {entries.slice(0, 8).map((entry) => (
              <button
                key={entry.id}
                className={styles.historyItem}
                onClick={() => navigate(ROUTES.results(entry.id), { state: { query: entry.query } })}
                title={entry.query}
              >
                <span className={styles.historyDot} />
                <span className={styles.historyText}>
                  {entry.query.length > 38 ? entry.query.slice(0, 38) + '…' : entry.query}
                </span>
              </button>
            ))}
          </div>
        )}

        <div className={styles.footer}>
          <button className={styles.abbreviationBtn} onClick={open} type="button">
            <div className={styles.abbreviationCopy}>
              <span className={styles.abbreviationLabel}>Abbreviations</span>
              <span className={styles.abbreviationHint}>Open the paper abbreviation bank</span>
            </div>
            {abbreviationCount > 0 && (
              <span className={styles.abbreviationBadge}>{abbreviationCount}</span>
            )}
          </button>
        </div>
      </aside>

      <AbbreviationsModal />
    </>
  )
}
