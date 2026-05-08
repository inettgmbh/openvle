import Info from '@theme/Admonition'
import clsx from 'clsx'
import styles from '@site/src/css/Prerequisites/styles.module.css'

export default function Prerequisites({
  items = [],
  note = null,
  showDivider = true,
}) {
  return (
    <div className={clsx(styles.container)}>
      {/* Liste */}
      {items.length > 0 && (
        <ul className={styles.list}>
          {items.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      )}

      {/* Optionaler Hinweis */}
      {note && (
        <div className={styles.noteWrapper}>
          <Info type="warning">{note}</Info>
        </div>
      )}

      {/* Divider */}
      {showDivider && <hr className={styles.divider} />}
    </div>
  )
}
