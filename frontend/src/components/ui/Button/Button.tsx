import type { ButtonHTMLAttributes, ReactNode } from 'react'

import styles from './Button.module.css'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost'
  size?: 'sm' | 'md'
  rightIcon?: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  rightIcon,
  children,
  className,
  ...props
}: ButtonProps) {
  const cls = [styles.btn, styles[variant], styles[size], className]
    .filter(Boolean)
    .join(' ')

  return (
    <button className={cls} {...props}>
      {children}
      {rightIcon && <span className={styles.iconRight}>{rightIcon}</span>}
    </button>
  )
}
