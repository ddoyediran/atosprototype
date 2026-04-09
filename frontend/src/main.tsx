import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import '@/styles/globals.css'
import { AppRouter } from '@/router/index'

const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error(
    'Root element #root not found. Check that index.html contains <div id="root"></div>.'
  )
}

createRoot(rootElement).render(
  <StrictMode>
    <AppRouter />
  </StrictMode>
)