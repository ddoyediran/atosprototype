import { lazy, Suspense } from 'react'
import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom'

import { Sidebar } from '@/components/layout/Sidebar/Sidebar'
import { MobileNav } from '@/components/layout/MobileNav/MobileNav'
import { SkeletonParagraph } from '@/components/ui/Skeleton/Skeleton'

import { ROUTES } from './routes'

// ─── Lazy-loaded pages ────────────────────────────────────────────────────────
// Code-split at the page level so the initial bundle stays lean.
const HomePage = lazy(() => import('@/pages/HomePage'))
const ResultsPage = lazy(() => import('@/pages/ResultsPage'))

// ─── Root layout ─────────────────────────────────────────────────────────────
function RootLayout() {
  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
      }}
    >
      <Sidebar />
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          minWidth: 0,
        }}
      >
        {/* Page content — TopBar is rendered inside each page so it can
            receive page-specific props (e.g. currentQuery) */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <Suspense fallback={<PageFallback />}>
            <Outlet />
          </Suspense>
        </div>
        <MobileNav />
      </div>
    </div>
  )
}

function PageFallback() {
  return (
    <div style={{ padding: '48px 40px' }}>
      <SkeletonParagraph lines={6} />
    </div>
  )
}

// ─── Router ───────────────────────────────────────────────────────────────────
const router = createBrowserRouter([
  {
    path: ROUTES.home,
    element: <RootLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: `${ROUTES.resultsBase}/:sessionId`, element: <ResultsPage /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}