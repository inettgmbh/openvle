import clsx from 'clsx'
import Heading from '@theme/Heading'
import styles from './styles.module.css'
import { translate } from '@docusaurus/Translate'

const FeatureList = [
  {
    title: translate({
      id: 'homepage.feature.easy-to-use.title',
      message: 'Einfach zu benutzen',
      description: 'Title of the `Easy to Use` feature',
    }),
    Svg: require('@site/static/img/server-web.svg').default,
    description: translate({
      id: 'homepage.feature.easy-to-use.description',
      message:
        'Benutzerfreundlichkeit steht im Vordergrund: Mit einer intuitiven Oberfläche vereinfacht die Anwendung komplexe Aufgaben wie die Verwaltung virtueller Maschinen und Ereignisse. Die nahtlose Integration verschiedener Dienste stellt sicher, dass Benutzer auch mit minimalen technischen Kenntnissen effizient arbeiten können.',
      description: 'Description of the `Easy to Use` feature',
    }),
  },
  {
    title: translate({
      id: 'homepage.feature.focus-on-what-matters.title',
      message: 'Konzentration auf das Wesentliche',
      description: 'Title of the `Focus on What Matters` feature',
    }),
    Svg: require('@site/static/img/server-cluster.svg').default,
    description: translate({
      id: 'homepage.feature.focus-on-what-matters.description',
      message:
        'Konzentrieren Sie sich auf das Wesentliche: Die vielseitige Anwendung unterstützt eine breite Palette von Arbeitsabläufen, von der Verwaltung virtueller Umgebungen bis hin zur Handhabung von Ereignissen und Benutzerberechtigungen. Dank ihres modularen Aufbaus lässt sie sich an unterschiedliche organisatorische Anforderungen anpassen und eignet sich somit für verschiedene Branchen und Anwendungsfälle.',
      description: 'Description of the `Focus on What Matters` feature',
    }),
  },
  {
    title: translate({
      id: 'homepage.feature.integrates-with-pve.title',
      message: 'Integriert mit Proxmox VE',
      description: 'Title of the `Integrates with Proxmox VE` feature',
    }),
    Svg: require('@site/static/img/proxmox.svg').default,
    description: translate({
      id: 'homepage.feature.integrates-with-pve.description',
      message:
        'Durch die Integration mit Proxmox VE wird der Lebenszyklus virtueller Maschinen verwaltet sowie Ressourcenzuweisung und Virtualisierung optimiert. Dies ermöglicht die Kontrolle virtueller Umgebungen für Veranstaltungen und Kurse und vereinfacht die Bereitstellung und Verwaltung von VMs erheblich.',
      description: 'Description of the `Integrates with Proxmox VE` feature',
    }),
  },
  {
    title: translate({
      id: 'homepage.feature.build-with-fastapi.title',
      message: 'Gebaut mit FastAPI auf Python 3',
      description: 'Title of the `Built with FastAPI on Python 3` feature',
    }),
    Svg: require('@site/static/img/python.svg').default,
    description: translate({
      id: 'homepage.feature.build-with-fastapi.description',
      message:
        'Entwickelt mit Python 3 und FastAPI, bietet das Backend eine leistungsstarke REST-API für die Verwaltung von Diensten und Daten. Mithilfe von SQLAlchemy für Datenbankinteraktionen und Pydantic für die Datenvalidierung gewährleistet es eine robuste Handhabung komplexer Geschäftslogik und Benutzereingaben.',
      description:
        'Description of the `Built with FastAPI on Python 3` feature',
    }),
  },
  {
    title: translate({
      id: 'homepage.feature.build-with-vuejs.title',
      message: 'Gebaut mit Vue.js',
      description: 'Title of the `Built with Vue.js` feature',
    }),
    Svg: require('@site/static/img/vuejs.svg').default,
    description: translate({
      id: 'homepage.feature.build-with-vuejs.description',
      message:
        'Das Frontend basiert auf Vue.js 3 und nutzt reaktive Komponenten sowie die Composition API für effiziente Zustandsverwaltung und dynamische Benutzeroberflächen. Dieses moderne Framework ermöglicht ein reibungsloses, reaktionsschnelles Erlebnis und integriert sich nahtlos mit den Backend-Diensten von OpenVLE, um Echtzeitdaten und Benutzerinteraktionen darzustellen.',
      description: 'Description of the `Built with Vue.js` feature',
    }),
  },

  {
    title: translate({
      id: 'homepage.feature.integrates-with-guacamole.title',
      message: 'Integriert mit Apache Guacamole',
      description: 'Title of the `Integrates with Apache Guacamole` feature',
    }),
    Svg: require('@site/static/img/guacamole.svg').default,
    description: translate({
      id: 'homepage.feature.integrates-with-guacamole.description',
      message:
        'Durch die Anbindung an Apache Guacamole wird ein nahtloser Fernzugriff auf virtuelle Maschinen über browserbasierte Verbindungen ermöglicht. Anwender können sich einfach mit VMs verbinden, ohne zusätzliche Software zu benötigen, indem sie vorkonfigurierte, vom System verwaltete Verbindungsprofile nutzen.',
      description:
        'Description of the `Integrates with Apache Guacamole` feature',
    }),
  },
]

function Feature({ Svg, title, description }) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  )
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  )
}
