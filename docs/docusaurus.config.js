// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import { themes as prismThemes } from 'prism-react-renderer'

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'OpenVLE',
  tagline: 'Dokumentation',
  favicon: 'img/logo.svg',

  url: 'https://docs.openvle.org',
  baseUrl: '/',

  onBrokenLinks: 'ignore',

  i18n: {
    defaultLocale: 'de',
    locales: ['de', 'en', 'fr'],
  },

  markdown: {
    format: 'detect',
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },
  themes: ['@docusaurus/theme-mermaid'],

  plugins: [
    [
      require.resolve('docusaurus-lunr-search'),
      {
        languages: ['de', 'en', 'fr'],
      },
    ],
    [
      '@docusaurus/plugin-client-redirects',
      {
        createRedirects(existingPath) {
          if (existingPath.includes('/usage/openvle/')) {
            return [existingPath.replace('/usage/openvle/', '/usage/kvs/')]
          }
          return undefined
        },
      },
    ],
  ],

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          editLocalizedFiles: true,
          editCurrentVersion: false,
          editUrl: 'https://github.com/inettgmbh/openvle/tree/main/docs/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/logo.svg',
      docs: {
        versionPersistence: 'localStorage',
        sidebar: {
          autoCollapseCategories: true,
          hideable: true,
        },
      },
      colorMode: {
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: process.env.PRODUCT_NAME,
        hideOnScroll: true,
        logo: {
          alt: 'Logo',
          src: 'img/logo.svg',
          srcDark: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'docsUsage',
            position: 'left',
            label: 'Benutzung',
          },
          {
            type: 'docSidebar',
            sidebarId: 'docsAdmins',
            position: 'left',
            label: 'Administration',
          },
          {
            type: 'docSidebar',
            sidebarId: 'docsChangelogs',
            position: 'left',
            label: 'Changelogs',
          },
          {
            type: 'docsVersionDropdown',
            position: 'right',
          },
          {
            type: 'localeDropdown',
            position: 'right',
          },
          {
            href: 'https://github.com/inettgmbh/openvle',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Dokumentationen',
            items: [
              {
                label: 'Benutzung',
                to: '/docs/usage/openvle/',
              },
              {
                label: 'Administration',
                to: '/docs/admin/infrastructure/',
              },
              {
                label: 'Changelogs',
                to: '/docs/changelogs',
              },
            ],
          },
          {
            title: 'Socials',
            items: [
              {
                label: 'Facebook',
                href: 'https://facebook.com/inettgmbh',
              },
              {
                label: 'Kontakt',
                href: 'https://www.inett.de/kontakt/',
              },
              {
                label: 'LinkedIn',
                href: 'https://linkedin.com/company/inett-gmbh',
              },
            ],
          },
          {
            title: 'Mehr',
            items: [
              {
                label: 'inett GmbH',
                href: 'https://www.inett.de',
              },
              {
                label: 'Impressum',
                href: 'https://www.inett.de/impressum',
              },
              {
                label: 'Datenschutz',
                href: 'https://www.inett.de/datenschutz',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} ${process.env.COPYRIGHT_HOLDER}. OpenVLE — souverän, Open Source, aus Europa.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'powershell'],
      },
      tableOfContents: {
        minHeadingLevel: 2,
        maxHeadingLevel: 5,
      },
      mermaid: {
        theme: {
          light: 'neutral',
          dark: 'dark',
        },
      },
    }),
}

export default config
