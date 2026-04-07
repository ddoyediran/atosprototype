import { useLocation } from 'react-router-dom'

import { Button } from '@/components/ui/Button/Button'
import { Icon } from '@/components/ui/Icon/Icon'
import { ROUTES } from '@/router/routes'

import styles from './TopBar.module.css'

interface TopBarProps {
  currentQuery?: string
}

export function TopBar({ currentQuery }: TopBarProps) {
  const location = useLocation()
  const isResults = location.pathname.startsWith(ROUTES.resultsBase)

  return (
    <header className={styles.topbar}>
      <span className={styles.title}>
        {isResults && currentQuery ? currentQuery : 'CAPMED-SCI'}
      </span>

      {isResults && (
        <div className={styles.actions}>
          <Button
            variant="ghost"
            size="sm"
            rightIcon={<Icon name="download" size={14} />}
          >
            Export PDF
          </Button>
        </div>
      )}
    </header>
  )
}
