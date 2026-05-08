import clsx from 'clsx'
import Info from '@theme/Admonition'
import styles from '@site/src/css/DocStatus.module.css'
import Link from '@docusaurus/Link'
import Translate, { translate } from '@docusaurus/Translate'

export default function DocStatus({
  status = 'stable',
  maintenance = false,
  security = false,
  showNotice = false,
}) {
  const labelMap = {
    stable: translate({ id: 'docStatus.stable', message: 'Stabil' }),
    draft: translate({ id: 'docStatus.draft', message: 'In Bearbeitung' }),
    deprecated: translate({ id: 'docStatus.deprecated', message: 'Veraltet' }),
  }

  return (
    <>
      {/* Status-Bereich */}
      <div className={clsx(styles.container)}>
        <span className={clsx(styles.badge, styles[status])}>
          {labelMap[status] || status}
        </span>

        {maintenance && (
          <span className={clsx(styles.badge, styles.maintenance)}>
            <Translate>Wartungskritisch</Translate>
          </span>
        )}

        {security && (
          <span className={clsx(styles.badge, styles.security)}>
            <Translate>Sicherheitsrelevant</Translate>
          </span>
        )}
      </div>

      {/* Release-Info-Bereich */}
      {showNotice && (
        <Info type="info">
          <p>
            <Translate>
              OpenVLE befindet sich aktuell in der letzten Testphase und wurde
              noch nicht offiziell veröffentlicht.
            </Translate>
            <br />
            <Translate>
              Daher funktionieren einige in dieser Dokumentation erwähnten
              GitHub-Links möglicherweise noch nicht.
            </Translate>
          </p>

          <p>
            <Translate>
              Wenn Sie bereits jetzt mehr erfahren möchten, erreichen Sie uns
              jederzeit
            </Translate>{' '}
            <Link to="https://www.inett.de/kontakt/">
              <Translate>hier</Translate>
            </Link>
          </p>
        </Info>
      )}
    </>
  )
}
