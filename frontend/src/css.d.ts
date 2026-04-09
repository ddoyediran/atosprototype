// Tells TypeScript that CSS Module imports are valid and return
// a record of class name strings. Vite handles the actual transformation.
declare module '*.module.css' {
  const classes: Record<string, string>
  export default classes
}

// Plain CSS imports (e.g. globals.css) — no value, side-effect only
declare module '*.css' {
  const content: undefined
  export default content
}