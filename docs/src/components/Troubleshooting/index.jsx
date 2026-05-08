import React from 'react'
import TroubleshootingItem from './Item'
import clsx from 'clsx'
import styles from './styles.module.css'
import Info from '@theme/Admonition'

export default function Troubleshooting({ intro = null, issues = [] }) {
  return (
    <div className={clsx(styles.container)}>
      {intro && (
        <div className={styles.introWrapper}>
          <Info type="info">{intro}</Info>
        </div>
      )}

      {issues.map((issue, index) => (
        <TroubleshootingItem key={index} {...issue} />
      ))}
    </div>
  )
}
