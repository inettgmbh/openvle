import React from 'react'
import Info from '@theme/Admonition'
import Link from '@docusaurus/Link'
import Translate from '@docusaurus/Translate'
import clsx from 'clsx'
import styles from './styles.module.css'

export default function TroubleshootingItem({
  description = null,
  cause = null,
  solution = [],
  tips = [],
  example = null,
  links = [],
}) {
  return (
    <div className={clsx(styles.item)}>
      {/* Beschreibung */}
      {description && <p className={styles.description}>{description}</p>}

      {/* Ursache */}
      {cause && (
        <div className={styles.block}>
          <Info type="info">
            <strong>
              <Translate id="troubleshooting.cause">Ursache:</Translate>
            </strong>{' '}
            {cause}
          </Info>
        </div>
      )}

      {/* Lösungs-Schritte */}
      {solution.length > 0 && (
        <div className={styles.block}>
          <strong>
            <Translate id="troubleshooting.solution">Lösung:</Translate>
          </strong>
          <ul className={styles.list}>
            {solution.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Tipps */}
      {tips.length > 0 && (
        <div className={styles.block}>
          <Info type="tip">
            <ul className={styles.tipList}>
              {tips.map((tip, idx) => (
                <li key={idx}>{tip}</li>
              ))}
            </ul>
          </Info>
        </div>
      )}

      {/* Beispiel / Codeblock */}
      {example && <div className={styles.example}>{example}</div>}

      {/* Weiterführende Links */}
      {links.length > 0 && (
        <div className={styles.block}>
          <strong>
            <Translate id="troubleshooting.links">
              Weiterführende Links:
            </Translate>
          </strong>
          <ul className={styles.linkList}>
            {links.map((link, idx) => (
              <li key={idx}>
                <Link to={link.href}>{link.label}</Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
