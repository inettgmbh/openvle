import styles from '@site/src/css/DocLastUpdated.module.css'
import Translate from '@docusaurus/Translate'

export default function DocLastUpdated({ date }) {
  if (!date) return null

  return (
    <div className={styles.container}>
      <span className={styles.item}>
        <strong>
          <Translate>Letzte Aktualisierung:</Translate>
        </strong>{' '}
        {date}
      </span>
    </div>
  )
}
