import {
  mdiAccount,
  mdiApplicationBrackets,
  mdiCalendar,
  mdiCalendarOutline,
  mdiClock,
  mdiClockOutline,
  mdiCodeNotEqualVariant,
  mdiConsole,
  mdiCounter,
  mdiCpu64Bit,
  mdiDomain,
  mdiEmailOutline,
  mdiEmailSync,
  mdiEyeOutline,
  mdiFilterOutline,
  mdiHarddisk,
  mdiIp,
  mdiKey,
  mdiLabel,
  mdiLanConnect,
  mdiListBoxOutline,
  mdiLock,
  mdiMailboxOutline,
  mdiMemory,
  mdiMonitor,
  mdiNumeric,
  mdiRename,
  mdiSchoolOutline,
  mdiServer,
  mdiShieldAccount,
  mdiTextBox,
  mdiTranslate,
  mdiVectorArrangeAbove,
  mdiWrench,
} from '@mdi/js'
import { computed } from 'vue'

import { SearchOperators } from '@/components/Tables/searchOperators'
import { getI18nT } from '@/i18n'
import backend from '@/services'

/**
 * Default icon used for fields without a custom icon.
 */
export const DEFAULT_FIELD_ICON = mdiFilterOutline

/**
 * Date/time field types that use picker inputs.
 */
export const DATE_TIME_TYPES = ['date', 'time', 'datetime']

/**
 * Returns standard search field presets with translated labels.
 *
 * @returns {Object} Map of preset definitions keyed by field name.
 */
function getSearchFieldPresets() {
  const t = getI18nT()
  return {
    name: {
      key: 'name',
      label: t('common.name'),
      icon: mdiRename,
      operators: SearchOperators.TEXT,
    },
    username: {
      key: 'username',
      label: t('components.searchPresets.username'),
      icon: mdiAccount,
      operators: SearchOperators.TEXT,
    },
    email: {
      key: 'email',
      label: t('components.searchPresets.email'),
      icon: mdiEmailOutline,
      operators: SearchOperators.TEXT,
    },
    description: {
      key: 'description',
      label: t('common.description'),
      icon: mdiTextBox,
      operators: SearchOperators.TEXT,
    },
    event: {
      key: 'event',
      label: t('objectTypes.event.singular'),
      icon: mdiCalendarOutline,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.events.search
      },
      get fetchSelected() {
        return backend.events.getName
      },
      labelAttribute: 'name',
      returnAttribute: 'id',
      minChars: 3,
    },
    course: {
      key: 'course',
      label: t('objectTypes.course.singular'),
      icon: mdiSchoolOutline,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.courses.search
      },
      get fetchSelected() {
        return backend.courses.getName
      },
      labelAttribute: 'name',
      returnAttribute: 'id',
      minChars: 3,
    },
    key: {
      key: 'key',
      label: t('common.key'),
      icon: mdiKey,
      operators: SearchOperators.TEXT,
    },
    vendor: {
      key: 'vendor',
      label: t('objectTypes.vendor.singular'),
      icon: mdiDomain,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.vendors.search
      },
      get fetchSelected() {
        return backend.vendors.getName
      },
      labelAttribute: 'name',
      returnAttribute: 'id',
      minChars: 3,
    },
    vm: {
      key: 'vm',
      label: t('objectTypes.virtualMachine.singular'),
      icon: mdiMonitor,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.vms.search
      },
      get fetchSelected() {
        return backend.vms.getName
      },
      labelAttribute: 'name',
      returnAttribute: 'id',
      minChars: 3,
    },
    template: {
      key: 'template',
      label: t('objectTypes.template.singular'),
      icon: mdiVectorArrangeAbove,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.templates.search
      },
      get fetchSelected() {
        return backend.templates.getName
      },
      labelAttribute: 'name',
      returnAttribute: 'id',
      minChars: 3,
    },
    os: {
      key: 'os',
      label: t('components.searchPresets.os'),
      icon: mdiApplicationBrackets,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.os.search
      },
      get fetchSelected() {
        return backend.os.getName
      },
      labelAttribute: 'name',
      returnAttribute: 'id',
      minChars: 3,
    },
    cpu: {
      key: 'cpu',
      label: t('components.searchPresets.cpu'),
      icon: mdiCpu64Bit,
      operators: SearchOperators.EQUALS_ONLY,
      suffix: 'Cores',
    },
    ram: {
      key: 'ram',
      label: t('components.searchPresets.ram'),
      icon: mdiMemory,
      operators: SearchOperators.EQUALS_ONLY,
      suffix: 'MB',
    },
    disk: {
      key: 'disk',
      label: t('components.searchPresets.disk'),
      icon: mdiHarddisk,
      operators: SearchOperators.EQUALS_ONLY,
      suffix: 'GB',
    },
    ipv4: {
      key: 'ipv4',
      label: t('components.searchPresets.ipv4'),
      icon: mdiIp,
      operators: SearchOperators.TEXT,
    },
    language: {
      key: 'language',
      label: t('components.searchPresets.language'),
      icon: mdiTranslate,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.languages.search
      },
      get fetchSelected() {
        return backend.languages.getName
      },
      labelAttribute: 'nameEnglish',
      returnAttribute: 'id',
      minChars: 2,
    },
    mailAction: {
      key: 'mail_action',
      label: t('objectTypes.mailAction.singular'),
      icon: mdiEmailSync,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.mailActions.search
      },
      get fetchSelected() {
        return backend.mailActions.formatById
      },
      labelAttribute: 'name',
      returnAttribute: 'id',
      minChars: 3,
    },
    status: {
      key: 'status',
      label: t('common.status'),
      icon: mdiListBoxOutline,
      operators: SearchOperators.EQUALS_ONLY,
    },
    protected: {
      key: 'protected',
      label: 'System',
      icon: mdiLock,
      operators: SearchOperators.EQUALS_ONLY,
    },
    preventDelete: {
      key: 'prevent_delete',
      label: t('common.protected'),
      icon: mdiLock,
      operators: SearchOperators.EQUALS_ONLY,
    },
    proxmoxId: {
      key: 'proxmoxId',
      label: 'Proxmox ID',
      icon: mdiNumeric,
      operators: SearchOperators.EQUALS_ONLY,
    },
    proxmoxNode: {
      key: 'proxmoxNode',
      label: 'Proxmox Node',
      icon: mdiServer,
      operators: SearchOperators.EQUALS_ONLY,
    },
    replyTo: {
      key: 'replyTo',
      label: t('components.searchPresets.replyTo'),
      icon: mdiEmailOutline,
      operators: SearchOperators.TEXT,
    },
    slug: {
      key: 'slug',
      label: t('components.searchPresets.slug'),
      icon: mdiKey,
      operators: SearchOperators.TEXT,
    },
    subject: {
      key: 'subject',
      label: t('components.searchPresets.subject'),
      icon: mdiMailboxOutline,
      operators: SearchOperators.TEXT,
    },
    label: {
      key: 'label',
      label: t('common.label'),
      icon: mdiLabel,
      operators: SearchOperators.TEXT,
    },
    protocol: {
      key: 'protocol',
      label: t('components.searchPresets.protocol'),
      icon: mdiLanConnect,
      operators: SearchOperators.EQUALS_ONLY,
    },
    authBackend: {
      key: 'authBackend',
      label: t('components.searchPresets.authBackend'),
      icon: mdiShieldAccount,
      operators: SearchOperators.EQUALS_ONLY,
    },
    visibility: {
      key: 'visibility',
      label: t('components.searchPresets.visibility'),
      icon: mdiEyeOutline,
      operators: SearchOperators.EQUALS_ONLY,
    },
    taskAction: {
      key: 'action',
      label: t('components.searchPresets.taskAction'),
      icon: mdiWrench,
      operators: SearchOperators.TEXT,
    },
    taskAttempt: {
      key: 'attempt',
      label: t('components.searchPresets.taskAttempt'),
      icon: mdiCounter,
      operators: SearchOperators.EQUALS_ONLY,
    },
    taskJobId: {
      key: 'job_id',
      label: t('components.searchPresets.taskJobId'),
      icon: mdiNumeric,
      operators: SearchOperators.TEXT,
    },
    taskResponseCode: {
      key: 'response_code',
      label: t('components.searchPresets.taskResponseCode'),
      icon: mdiCodeNotEqualVariant,
      operators: SearchOperators.TEXT,
    },
    taskResponseMessage: {
      key: 'response_message',
      label: t('components.searchPresets.taskResponseMessage'),
      icon: mdiConsole,
      operators: SearchOperators.TEXT,
    },
    createdAt: {
      key: 'createdAt',
      label: t('common.createdAt'),
      icon: mdiCalendar,
      type: 'datetime',
      operators: SearchOperators.DATE,
    },
    updatedAt: {
      key: 'updatedAt',
      label: t('common.updatedAt'),
      icon: mdiCalendar,
      type: 'datetime',
      operators: SearchOperators.DATE,
    },
    date: {
      key: 'date',
      label: t('common.date'),
      icon: mdiCalendar,
      type: 'date',
      operators: SearchOperators.DATE,
    },
    time: {
      key: 'time',
      label: t('components.searchPresets.time'),
      icon: mdiClockOutline,
      type: 'time',
      operators: SearchOperators.DATE,
    },
    datetime: {
      key: 'datetime',
      label: t('components.searchPresets.datetime'),
      icon: mdiClock,
      type: 'datetime',
      operators: SearchOperators.DATE,
    },
    createdById: {
      key: 'createdById',
      label: t('components.searchPresets.createdBy'),
      icon: mdiAccount,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.users.search
      },
      get fetchSelected() {
        return backend.users.formatById
      },
      labelAttribute: 'name',
      returnAttribute: 'id',
      minChars: 3,
    },
    updatedById: {
      key: 'updatedById',
      label: t('components.searchPresets.updatedBy'),
      icon: mdiAccount,
      type: 'lookup',
      operators: SearchOperators.EQUALS_ONLY,
      get fetchData() {
        return backend.users.search
      },
      get fetchSelected() {
        return backend.users.formatById
      },
      labelAttribute: 'name',
      returnAttribute: 'id',
      minChars: 3,
    },
  }
}

// Cached computed — re-evaluates only when locale changes
const searchFieldPresetsComputed = computed(() => getSearchFieldPresets())

/**
 * Proxy for SEARCH_FIELD_PRESETS that delegates to the cached computed.
 */
export const SEARCH_FIELD_PRESETS = new Proxy(
  {},
  {
    get(_, key) {
      return searchFieldPresetsComputed.value[key]
    },
    ownKeys() {
      return Object.keys(searchFieldPresetsComputed.value)
    },
    getOwnPropertyDescriptor(_, key) {
      const presets = searchFieldPresetsComputed.value
      if (key in presets) {
        return {
          configurable: true,
          enumerable: true,
          value: presets[key],
        }
      }
      return undefined
    },
  },
)

/**
 * Resolves field definitions by applying presets.
 * Presets are auto-applied based on field key, or explicitly via `preset` property.
 * Custom properties in the field definition will override preset defaults.
 *
 * @param {Array} fields - Array of field definitions
 * @returns {Array} - Array of resolved field definitions with presets applied
 */
export function resolveFieldPresets(fields) {
  const presets = searchFieldPresetsComputed.value
  return fields.map((field) => {
    const presetKey = field.preset ?? field.key
    const preset = presets[presetKey] ?? {}
    const resolved = { ...preset, ...field }

    // Auto-apply operators for specific field types if no operators specified
    if (!field.operators) {
      if (resolved.type === 'number') {
        resolved.operators = SearchOperators.NUMBER
      } else if (DATE_TIME_TYPES.includes(resolved.type)) {
        resolved.operators = SearchOperators.DATE
      }
    }

    return resolved
  })
}
