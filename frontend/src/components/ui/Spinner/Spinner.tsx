import styles from './Spinner.module.css'

interface SpinnerProps {
  size?: number
}

export function Spinner({ size = 16 }: SpinnerProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.5}
      strokeLinecap="round"
      className={styles.spinner}
      aria-hidden="true"
    >
      <path d="M12 2a10 10 0 1 0 10 10" />
    </svg>
  )
}
