import { useNavigate, useLocation } from 'react-router-dom'

import { Icon } from '@/components/ui/Icon/Icon'
import { ROUTES } from '@/router/routes'

import styles from './MobileNav.module.css'

export function MobileNav() {
  const navigate = useNavigate()
  const location = useLocation()
  const isHome = location.pathname === ROUTES.home

  return (
    <nav className={styles.nav} aria-label="Mobile navigation">
      <button
        className={`${styles.item} ${isHome ? styles.itemActive : ''}`}
        onClick={() => navigate(ROUTES.home)}
      >
        <Icon name="home" size={22} />
        <span className={styles.label}>Home</span>
      </button>
      <button
        className={`${styles.item} ${!isHome ? styles.itemActive : ''}`}
        onClick={() => navigate(ROUTES.home)}
      >
        <Icon name="history" size={22} />
        <span className={styles.label}>History</span>
      </button>
    </nav>
  )
}
