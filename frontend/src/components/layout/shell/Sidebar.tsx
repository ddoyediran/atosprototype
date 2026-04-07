import { useNavigate, useLocation } from 'react-router-dom'

import { Icon } from '@/components/ui/Icon/Icon'
import { useResearchHistory } from '@/hooks/useResearchHistory'
import { ROUTES } from '@/router/routes'

import styles from './Sidebar.module.css'

export function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { entries } = useResearchHistory()

  const isHome = location.pathname === ROUTES.home

  return (
    <aside className={styles.sidebar}>
      {/* Brand */}
      <div className={styles.brand}>
        <div className={styles.logo}>
          <Icon name="clinical" size={20} className={styles.logoIcon} />
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
    </aside>
  )
}