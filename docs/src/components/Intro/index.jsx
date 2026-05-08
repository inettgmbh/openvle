import Info from '@theme/Admonition'
import clsx from 'clsx'
import styles from '@site/src/css/Intro/styles.module.css'
import Translate from '@docusaurus/Translate'

export default function Intro({
  summary,
  audience = null,
  context = null,
  note = null,
  showDivider = true,
}) {
  return (
    <div className={clsx(styles.introContainer)}>
      {/* Summary */}
      {summary && <p className={styles.summary}>{summary}</p>}

      {/* Audience */}
      {audience && (
        <p className={styles.metaInfo}>
          <strong>
            <Translate>Zielgruppe:</Translate>
          </strong>{' '}
          {audience}
        </p>
      )}

      {/* Context */}
      {context && (
        <p className={styles.metaInfo}>
          <strong>
            <Translate>Kontext:</Translate>
          </strong>{' '}
          {context}
        </p>
      )}

      {/* Optionaler Hinweis */}
      {note && (
        <div className={styles.noteWrapper}>
          <Info type="note">{note}</Info>
        </div>
      )}

      {/* Divider */}
      {showDivider && <hr className={styles.divider} />}
    </div>
  )
}
