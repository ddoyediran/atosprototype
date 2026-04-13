import styles from './Skeleton.module.css'

interface SkeletonParagraphProps {
  lines?: number
}

export function SkeletonParagraph({ lines = 3 }: SkeletonParagraphProps) {
  return (
    <div className={styles.paragraph}>
      {Array.from({ length: lines }, (_, i) => (
        <div
          key={i}
          className={styles.line}
          style={{ width: i === lines - 1 ? '60%' : '100%' }}
        />
      ))}
    </div>
  )
}
