import { describe, expect, it } from 'vitest'

import fs from 'fs'
import path from 'path'

const LOCALES_DIR = path.resolve(__dirname, '../../src/locales')
const SRC_DIR = path.resolve(__dirname, '../../src')

const de = JSON.parse(
  fs.readFileSync(path.join(LOCALES_DIR, 'de.json'), 'utf8'),
)
const en = JSON.parse(
  fs.readFileSync(path.join(LOCALES_DIR, 'en.json'), 'utf8'),
)
const es = JSON.parse(
  fs.readFileSync(path.join(LOCALES_DIR, 'es.json'), 'utf8'),
)
const fr = JSON.parse(
  fs.readFileSync(path.join(LOCALES_DIR, 'fr.json'), 'utf8'),
)

// --- Helpers ---

function getLeafKeys(obj, prefix = '') {
  const keys = []
  for (const [k, v] of Object.entries(obj)) {
    const keyPath = prefix ? `${prefix}.${k}` : k
    if (typeof v === 'object' && v !== null) {
      keys.push(...getLeafKeys(v, keyPath))
    } else {
      keys.push(keyPath)
    }
  }
  return keys
}

function getLeafValue(obj, keyPath) {
  const parts = keyPath.split('.')
  let current = obj
  for (const part of parts) {
    if (current == null || typeof current !== 'object') return undefined
    current = current[part]
  }
  return current
}

function extractPlaceholders(str) {
  const matches = str.match(/\{[^}]+\}/g)
  return matches ? matches.sort() : []
}

function isAutoExcluded(value) {
  if (typeof value !== 'string') return true
  if (value.length <= 3) return true
  if (/^\d+([.,]\d+)?$/.test(value)) return true
  if (/^https?:\/\//.test(value)) return true
  // ALL CAPS / no lowercase letters (acronyms, abbreviations)
  if (/^[^a-zäöüàâéèêëïîôùûç]+$/.test(value)) return true
  return false
}

// Keys where identical values across locales are intentional.
// These have been reviewed and are correct (technical terms, proper nouns,
// English loanwords used in German, cognates between de/fr).
const IDENTICAL_VALUE_ALLOWLIST = new Set([
  // Common UI labels (English loanwords / cognates)
  'common.authBackend',
  'common.details',
  'common.hostname',
  'common.infos',
  'common.label',
  'common.name',
  'common.node',
  'common.port',
  'common.proxmox',
  'common.status',

  // Component labels
  'components.baseTags.tags',
  'components.baseTable.presets.name',
  'components.baseTable.presets.protected',
  'components.baseTable.presets.status',
  'components.changelog.fields.endpointUrl',
  'components.csvUpload.stepImport',
  'components.eventStatus.steps.archiving.title',
  'components.eventStatus.steps.deploying.title',
  'components.permissionChangesConfirm.global',
  'components.saveProgressModal.operationIndex',
  'components.searchPresets.authBackend',
  'components.tablePermissions.person',
  'components.tablePermissions.scopeGlobal',
  'components.tableProxmoxLogs.node',

  // Navigation
  'nav.proxmox',
  'nav.proxmoxNodes',
  'nav.scimClients',
  'nav.scimProviders',
  'nav.system',
  'nav.tags',
  'nav.tasks',

  // Object types
  'objectTypes.changelog.plural',
  'objectTypes.changelog.singular',
  'objectTypes.dashboard.plural',
  'objectTypes.dashboard.singular',
  'objectTypes.proxmox.plural',
  'objectTypes.proxmox.singular',
  'objectTypes.scimClient.plural',
  'objectTypes.scimClient.singular',
  'objectTypes.scimProvider.plural',
  'objectTypes.scimProvider.singular',
  'objectTypes.subtask.plural',
  'objectTypes.subtask.singular',
  'objectTypes.tag.plural',
  'objectTypes.task.plural',
  'objectTypes.task.singular',

  // Permissions
  'permissions.objectAdmins.short',
  'permissions.vm.actionsHibernate.short',

  // Route labels
  'routes.dashboard',
  'routes.login',
  'routes.oidcCallback',
  'routes.profile',
  'routes.proxmoxNodeDetail',
  'routes.proxmoxNodeList',
  'routes.scimClientsDetail',
  'routes.scimClientsList',
  'routes.scimProvidersDetail',
  'routes.scimProvidersList',
  'routes.subtasksDetail',
  'routes.tagsList',
  'routes.tasksDetail',
  'routes.tasksList',

  // Status labels (English terms used across locales)
  'status.cloning',
  'status.deploying',
  'status.paused',
  'status.running',
  'status.starting',
  'status.stopped',
  'status.stopping',
  'status.system',

  // Tooltips
  'tooltips.systemSettingVisibility.admins',

  // Name placeholders (technical terms / proper nouns)
  'views.applications.form.namePlaceholder',
  'views.connections.detail.namePlaceholder',
  'views.guacamole.form.namePlaceholder',
  'views.os.form.namePlaceholder',
  'views.templates.form.namePlaceholder',
  'views.vendors.form.namePlaceholder',
  'views.vms.namePlaceholder',

  // View-specific labels
  'views.activities.detail.parameter',
  'views.activities.detail.requestHeaders',
  'views.activities.detail.responseHeaders',
  'views.changelogs.list.changelogs',
  'views.dashboard.title',
  'views.events.detail.columns.person',
  'views.guacamole.detail.reprovision',
  'views.mailActions.detail.invalidVariablesWarning',
  'views.mails.list.title',
  'views.policies.agree.logout',
  'views.tags.list.nameLabel',
  'views.templates.import.proxmoxId',
  'views.userProfile.title',
  'views.users.detail.accountStatus',
  'views.users.form.locale',
  'views.vms.detail.actions.reset',
  'components.searchPresets.taskJobId',
  'visibility.admins',
])

// Key prefixes where identical values are expected (technical/metric labels)
const IDENTICAL_VALUE_PREFIX_ALLOWLIST = [
  'components.metricsSelectionPanel.',
  'components.proxmoxRrdChart.',
  'views.proxmox.',
  'views.scimClients.',
  'views.scimProviders.',
  'views.tasks.',
]

function isAllowlisted(keyPath, value) {
  if (isAutoExcluded(value)) return true
  if (IDENTICAL_VALUE_ALLOWLIST.has(keyPath)) return true
  for (const prefix of IDENTICAL_VALUE_PREFIX_ALLOWLIST) {
    if (keyPath.startsWith(prefix)) return true
  }
  return false
}

// --- Key sets ---

const deKeys = getLeafKeys(de).sort()
const enKeys = getLeafKeys(en).sort()
const esKeys = getLeafKeys(es).sort()
const frKeys = getLeafKeys(fr).sort()

// --- Tests ---

describe('i18n locale validation', () => {
  describe('structural completeness', () => {
    it('de, en, es and fr have identical key sets', () => {
      const deSet = new Set(deKeys)
      const enSet = new Set(enKeys)
      const esSet = new Set(esKeys)
      const frSet = new Set(frKeys)

      const missingInEn = deKeys.filter((k) => !enSet.has(k))
      const missingInEs = deKeys.filter((k) => !esSet.has(k))
      const missingInFr = deKeys.filter((k) => !frSet.has(k))
      const missingInDe = [
        ...enKeys.filter((k) => !deSet.has(k)),
        ...esKeys.filter((k) => !deSet.has(k)),
        ...frKeys.filter((k) => !deSet.has(k)),
      ]

      expect(missingInEn, 'Keys in de.json but missing in en.json').toEqual([])
      expect(missingInEs, 'Keys in de.json but missing in es.json').toEqual([])
      expect(missingInFr, 'Keys in de.json but missing in fr.json').toEqual([])
      expect(missingInDe, 'Keys in en/es/fr but missing in de.json').toEqual([])
    })

    it('no locale file contains empty string values', () => {
      const emptyDe = deKeys.filter((k) => getLeafValue(de, k) === '')
      const emptyEn = enKeys.filter((k) => getLeafValue(en, k) === '')
      const emptyEs = esKeys.filter((k) => getLeafValue(es, k) === '')
      const emptyFr = frKeys.filter((k) => getLeafValue(fr, k) === '')

      expect(emptyDe, 'Empty values in de.json').toEqual([])
      expect(emptyEn, 'Empty values in en.json').toEqual([])
      expect(emptyEs, 'Empty values in es.json').toEqual([])
      expect(emptyFr, 'Empty values in fr.json').toEqual([])
    })

    it('placeholder parameters are consistent across locales', () => {
      const mismatches = []

      for (const key of deKeys) {
        const deVal = getLeafValue(de, key)
        const enVal = getLeafValue(en, key)
        const esVal = getLeafValue(es, key)
        const frVal = getLeafValue(fr, key)

        if (
          typeof deVal !== 'string' ||
          typeof enVal !== 'string' ||
          typeof esVal !== 'string' ||
          typeof frVal !== 'string'
        ) {
          continue
        }

        const dePlaceholders = extractPlaceholders(deVal)
        const enPlaceholders = extractPlaceholders(enVal)
        const esPlaceholders = extractPlaceholders(esVal)
        const frPlaceholders = extractPlaceholders(frVal)

        if (
          JSON.stringify(dePlaceholders) !== JSON.stringify(enPlaceholders) ||
          JSON.stringify(dePlaceholders) !== JSON.stringify(esPlaceholders) ||
          JSON.stringify(dePlaceholders) !== JSON.stringify(frPlaceholders)
        ) {
          mismatches.push({
            key,
            de: dePlaceholders,
            en: enPlaceholders,
            es: esPlaceholders,
            fr: frPlaceholders,
          })
        }
      }

      expect(
        mismatches,
        'Placeholder mismatch:\n' +
          mismatches
            .map(
              (m) =>
                `  ${m.key}: de=${JSON.stringify(m.de)} en=${JSON.stringify(m.en)} es=${JSON.stringify(m.es)} fr=${JSON.stringify(m.fr)}`,
            )
            .join('\n'),
      ).toEqual([])
    })
  })

  describe('untranslated value detection', () => {
    it('de values differ from en values (no untranslated keys)', () => {
      const identical = deKeys.filter((key) => {
        const deVal = getLeafValue(de, key)
        const enVal = getLeafValue(en, key)
        if (deVal !== enVal) return false
        return !isAllowlisted(key, deVal)
      })

      expect(
        identical,
        'Keys where de === en (possibly untranslated):\n' +
          identical.map((k) => `  ${k}: "${getLeafValue(de, k)}"`).join('\n'),
      ).toEqual([])
    })

    it('de values differ from es values (no untranslated keys)', () => {
      const identical = deKeys.filter((key) => {
        const deVal = getLeafValue(de, key)
        const esVal = getLeafValue(es, key)
        if (deVal !== esVal) return false
        return !isAllowlisted(key, deVal)
      })

      expect(
        identical,
        'Keys where de === es (possibly untranslated):\n' +
          identical.map((k) => `  ${k}: "${getLeafValue(de, k)}"`).join('\n'),
      ).toEqual([])
    })

    it('de values differ from fr values (no untranslated keys)', () => {
      const identical = deKeys.filter((key) => {
        const deVal = getLeafValue(de, key)
        const frVal = getLeafValue(fr, key)
        if (deVal !== frVal) return false
        return !isAllowlisted(key, deVal)
      })

      expect(
        identical,
        'Keys where de === fr (possibly untranslated):\n' +
          identical.map((k) => `  ${k}: "${getLeafValue(de, k)}"`).join('\n'),
      ).toEqual([])
    })
  })

  describe('source code key coverage', () => {
    function getAllSourceFiles(dir, extensions = ['.vue', '.js']) {
      const results = []
      const entries = fs.readdirSync(dir, { withFileTypes: true })
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name)
        if (entry.isDirectory() && entry.name !== 'node_modules') {
          results.push(...getAllSourceFiles(fullPath, extensions))
        } else if (extensions.some((ext) => entry.name.endsWith(ext))) {
          results.push(fullPath)
        }
      }
      return results
    }

    function extractKeysFromSource(content) {
      const keys = new Set()
      // Match t('key.path') and $t('key.path') — key must contain a dot
      const tCallRegex =
        /\$?t\(\s*'([a-zA-Z][a-zA-Z0-9]*(?:\.[a-zA-Z][a-zA-Z0-9]*)+)'/g
      let match
      while ((match = tCallRegex.exec(content)) !== null) {
        keys.add(match[1])
      }
      // Match labelKey/titleKey/key property assignments
      const propRegex =
        /(?:labelKey|titleKey)\s*:\s*'([a-zA-Z][a-zA-Z0-9]*(?:\.[a-zA-Z][a-zA-Z0-9]*)+)'/g
      while ((match = propRegex.exec(content)) !== null) {
        keys.add(match[1])
      }
      return keys
    }

    it('all keys used in source code exist in locale files', () => {
      const sourceFiles = getAllSourceFiles(SRC_DIR)
      const deKeySet = new Set(deKeys)
      const allUsedKeys = new Set()

      for (const file of sourceFiles) {
        const content = fs.readFileSync(file, 'utf8')
        const keys = extractKeysFromSource(content)
        for (const key of keys) {
          allUsedKeys.add(key)
        }
      }

      // A key is valid if it exists as a leaf key OR as a parent prefix
      // (vue-i18n supports referencing parent objects)
      const keyExistsOrIsPrefix = (key) => {
        if (deKeySet.has(key)) return true
        const prefix = key + '.'
        return deKeys.some((k) => k.startsWith(prefix))
      }

      const missingKeys = [...allUsedKeys]
        .filter((key) => !keyExistsOrIsPrefix(key))
        .sort()

      expect(
        missingKeys,
        'Keys used in source code but missing in de.json:\n' +
          missingKeys.map((k) => `  ${k}`).join('\n'),
      ).toEqual([])
    })
  })
})
