/**
 * Extract citation numbers from a markdown answer string.
 * Handles [1], [2,3], [1,2,3] formats.
 */
export function extractCitationNumbers(text: string): number[] {
  const pattern = /\[(\d+(?:,\s*\d+)*)\]/g
  const found = new Set<number>()
  let match: RegExpExecArray | null

  while ((match = pattern.exec(text)) !== null) {
    match[1].split(',').forEach((n) => found.add(parseInt(n.trim(), 10)))
  }

  return Array.from(found).sort((a, b) => a - b)
}

/**
 * Format authors list for display.
 * Shows first `maxAuthors` names, appends "et al." if truncated.
 */
export function formatAuthors(authors: string[], maxAuthors = 3): string {
  if (!authors.length) return 'Unknown authors'
  const shown = authors.slice(0, maxAuthors)
  const suffix = authors.length > maxAuthors ? ' et al.' : ''
  return shown.join(', ') + suffix
}

/**
 * Generate a URL-safe session ID for research sessions.
 * Uses the browser's built-in crypto — no external dependency needed.
 */
export function generateSessionId(): string {
  const arr = new Uint8Array(8)
  crypto.getRandomValues(arr)
  return Array.from(arr, (b) => b.toString(16).padStart(2, '0')).join('')
}