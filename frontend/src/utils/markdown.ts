/**
 * Lightweight Markdown → HTML renderer.
 *
 * Intentionally minimal — only handles the subset of Markdown that the
 * backend's OpenAI prompt produces. We avoid a full MD library to keep the
 * bundle small and to retain full control over citation chip rendering.
 *
 * Supported:
 *   **bold**, *italic*, `code`
 *   # / ## / ### headings
 *   - / * unordered lists
 *   [1], [1,2,3] citation markers → citation chip spans
 *   \n\n paragraph breaks
 */

/**
 * Render a Markdown string to an HTML string.
 * The output is intended for use with dangerouslySetInnerHTML — ensure the
 * source is always the backend LLM response, never user-supplied raw text.
 */
export function renderMarkdown(text: string): string {
  if (!text) return ''

  let html = text

  // ── Headings (must come before bold to avoid ** conflicts) ────────────────
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>')

  // ── Inline formatting ─────────────────────────────────────────────────────
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/`(.+?)`/g, '<code class="md-code">$1</code>')

  // ── Citation markers → chips ──────────────────────────────────────────────
  // Matches [1: Abstract, 3: Background, 5: Abstract] — renders each entry as its own chip
  html = html.replace(
    /\[(\d+:\s*[^\],]+(?:,\s*\d+:\s*[^\],]+)*)\]/g,
    (_match, inner: string) => {
      const chips = inner.split(/,\s*(?=\d+:)/).map((entry) => {
        const m = entry.match(/^(\d+):\s*(.+)$/)
        if (!m) return entry
        const [, num, section] = m
        return `<span class="citation-chip" data-citation="${num}">${num}: ${section.trim()}</span>`
      })
      return `[${chips.join(', ')}]`
    }
  )

  // ── Unordered lists ───────────────────────────────────────────────────────
  // Collect consecutive list lines and wrap in <ul>
  html = html.replace(/(^[-*] .+$\n?)+/gm, (block) => {
    const items = block
      .trim()
      .split('\n')
      .map((line) => `<li>${line.replace(/^[-*] /, '')}</li>`)
      .join('')
    return `<ul class="md-list">${items}</ul>\n`
  })

  // ── Paragraphs ────────────────────────────────────────────────────────────
  // Split on double newlines; skip blocks that are already block elements
  const paragraphs = html.split(/\n\n+/)
  html = paragraphs
    .map((block) => {
      const trimmed = block.trim()
      if (!trimmed) return ''
      // Don't wrap headings, lists, or already-wrapped elements in <p>
      if (/^<(h[1-6]|ul|ol|li|blockquote)/.test(trimmed)) return trimmed
      return `<p class="md-p">${trimmed.replace(/\n/g, '<br />')}</p>`
    })
    .join('\n')

  return html
}