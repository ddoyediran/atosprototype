/**
 * All application routes defined in one place.
 * Import from here — never hardcode path strings in components.
 */
export const ROUTES = {
  home: '/',
  resultsBase: '/research',
  results: (sessionId: string) => `/research/${sessionId}`,
} as const