<script setup>
import { mdiScriptTextOutline } from '@mdi/js'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseTable from '@/components/BaseTable.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import ChangelogChangesCell from '@/components/Tables/ChangelogChangesCell.vue'
import { SearchOperators } from '@/components/Tables/searchOperators'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'
import {
  resolveFieldFromLookup,
  resolveObjectTypeToGerman,
} from '@/utils/dataUtils'
import { getObjectPermissionByKey } from '@/utils/objectModelPermissions'

// Props
const props = defineProps({
  objectId: {
    type: String,
    default: null,
  },
  objectType: {
    type: String,
    default: null,
  },
  all: Boolean,
  perPage: {
    type: Number,
    required: true,
  },
})

const { t } = useI18n()

// State
const dataLoading = ref(true)
const lookupStore = useLookupStore()
const objects = ref([])
const totalCount = ref(0)

const pagination = ref({
  currentPage: 1,
  sortColumnKey: 'timestamp',
  sortDirection: 'desc',
  perPage: props.perPage,
  searchField: null,
  searchValue: null,
})

// Custom labels for field keys
const FIELD_LABELS = computed(() => ({
  active: t('components.changelog.fields.active'),
  content: t('components.changelog.fields.content'),
  contenthtml: t('components.changelog.fields.contentHtml'),
  course: t('components.changelog.fields.course'),
  cpu: t('components.changelog.fields.cpu'),
  dateend: t('components.changelog.fields.dateEnd'),
  datestart: t('components.changelog.fields.dateStart'),
  defaultuserstatus: t('components.changelog.fields.defaultUserStatus'),
  description: t('components.changelog.fields.description'),
  enabled: t('components.changelog.fields.enabled'),
  endpointurl: t('components.changelog.fields.endpointUrl'),
  language: t('components.changelog.fields.language'),
  mailaction: t('components.changelog.fields.mailAction'),
  moodlecourseid: t('components.changelog.fields.moodleCourseId'),
  os: t('components.changelog.fields.os'),
  permissions: t('components.changelog.fields.permissions'),
  preventdelete: t('components.changelog.fields.protected'),
  protected: t('components.changelog.fields.protected'),
  ram: t('components.changelog.fields.ram'),
  replyto: t('components.changelog.fields.replyTo'),
  roles: t('components.changelog.fields.roles'),
  subject: t('components.changelog.fields.subject'),
  syncgroups: t('components.changelog.fields.syncGroups'),
  templates: t('components.changelog.fields.templates'),
  timeend: t('components.changelog.fields.timeEnd'),
  timestart: t('components.changelog.fields.timeStart'),
  vendor: t('components.changelog.fields.vendor'),
}))

// Resolve permission key to label from OBJECT_PERMISSIONS
function resolvePermissionKeyLabel(key) {
  return getObjectPermissionByKey(key)?.label || key
}

// Columns configuration for BaseTable
const columns = computed(() => [
  {
    label: t('components.changelog.columns.changedBy'),
    key: 'username',
    sortKey: 'userId',
    width: '180px',
    formatter: (value) => value || t('components.changelog.columns.unknown'),
  },
  {
    label: t('components.changelog.columns.change'),
    key: 'parsedChanges',
    sortable: false,
    width: '400px',
  },
])

// Value parsing and formatting
function toValidJson(str) {
  if (!str) return null

  return str
    .replace(/'/g, '"')
    .replace(/\bFalse\b/g, 'false')
    .replace(/\bTrue\b/g, 'true')
    .replace(/\bNone\b/g, 'null')
    .replace(/UUID\("([^"]+)"\)/g, '"$1"')
    .replace(/UUID\('([^']+)'\)/g, '"$1"')
    .replace(/datetime\.date\((\d+), (\d+), (\d+)\)/g, (_, y, m, d) => {
      return `"${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}"`
    })
    .replace(/datetime\.time\((\d+), (\d+)(?:, (\d+))?\)/g, (_, h, m, s) => {
      return `"${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s ?? '0').padStart(2, '0')}"`
    })
}

// Extract permission entries from malformed Python representations
function extractPermissionsFromRaw(str) {
  if (!str || !str.includes('permissions')) return null

  if (/permissions['"]\s*:\s*\[\s*\]/.test(str)) {
    return { permissions: '' }
  }

  const entryRegex =
    /object_type['"]?\s*:\s*['"]?(\w+)['"]?[^}]*?permission_key['"]?\s*:\s*['"]?(\w+)['"]?/g
  // Matches object_id in quoted, UUID()-wrapped, or bare (unquoted) form
  const objectIdRegex =
    /object_id['"]?\s*:\s*(?:UUID\(['"]([^'"]+)['"]\)|['"]([a-f0-9-]+)['"]|([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})|None|null)/
  const permissions = []
  let match
  while ((match = entryRegex.exec(str)) !== null) {
    // Find the enclosing { } block to also extract object_id
    const blockStart = str.lastIndexOf('{', match.index)
    const blockEnd = str.indexOf('}', match.index)
    const block =
      blockStart >= 0 && blockEnd >= 0
        ? str.slice(blockStart, blockEnd + 1)
        : match[0]
    const idMatch = objectIdRegex.exec(block)

    permissions.push({
      object_type: match[1],
      object_id: idMatch
        ? idMatch[1] || idMatch[2] || idMatch[3] || null
        : null,
      permission_key: match[2],
    })
  }

  return permissions.length > 0 ? { permissions } : null
}

function replaceEmptyArrays(obj) {
  const newObj = {}
  for (const [key, value] of Object.entries(obj)) {
    if ((Array.isArray(value) && value.length === 0) || value === null) {
      newObj[key] = ''
    } else {
      newObj[key] = value
    }
  }
  return newObj
}

function safeParse(str) {
  if (!str) return {}

  const converted = toValidJson(str)
  if (!converted) return {}

  if (/object at 0x/i.test(converted)) {
    return 'UNKWN'
  }

  try {
    return replaceEmptyArrays(JSON.parse(converted))
  } catch {
    try {
      return JSON.parse([converted])
    } catch {
      try {
        // Try permission extraction as fallback for malformed data
        const permResult = extractPermissionsFromRaw(str)
        if (permResult) return permResult

        // Policy content handling
        if (!converted.includes('content')) {
          return 'UNKWN'
        }

        const escapedContent = converted
          .replace('{"content": "', '')
          .replace('"}', '')
          .replace(/\\/g, '\\\\')
          .replace(/"/g, '\\"')
          .replace(/\n/g, '\\n')
        const validJson = `{"content": "${escapedContent}"}`
        return JSON.parse(validJson)
      } catch {
        return 'UNKWN'
      }
    }
  }
}

function normalize(val) {
  if (typeof val === 'string') return val.trim()
  if (typeof val === 'number' || typeof val === 'boolean') return val
  if (val === null || val === undefined) return null
  return JSON.stringify(val)
}

function parseChanges(log) {
  const oldValue = safeParse(log.valueOld)
  const newValue = safeParse(log.valueNew)

  if (oldValue === 'UNKWN' && newValue === 'UNKWN') {
    return [
      {
        key: 'Raw-Diff',
        oldValue: 'UNKWN',
        newValue: 'UNKWN',
        isRaw: true,
      },
    ]
  }

  const allKeys = new Set([
    ...(typeof oldValue === 'object' && oldValue !== null
      ? Object.keys(oldValue)
      : []),
    ...(typeof newValue === 'object' && newValue !== null
      ? Object.keys(newValue)
      : []),
  ])

  return Array.from(allKeys).flatMap((key) => {
    const isOldObj = typeof oldValue === 'object' && oldValue !== null
    const isNewObj = typeof newValue === 'object' && newValue !== null

    const rawOld = isOldObj ? (oldValue[key] ?? 'UNKWN') : 'UNKWN'
    const rawNew = isNewObj ? (newValue[key] ?? 'UNKWN') : 'UNKWN'

    if (normalize(rawOld) === normalize(rawNew)) {
      return []
    }

    const change = { key, oldValue: rawOld, newValue: rawNew, isRaw: false }

    // Enrich permission changes with display metadata
    if (key === 'permissions') {
      const perm =
        (Array.isArray(rawNew) && rawNew.length > 0 && rawNew[0]) ||
        (Array.isArray(rawOld) && rawOld.length > 0 && rawOld[0]) ||
        null

      if (perm && 'permission_key' in perm) {
        change.isPermission = true
        change.added = Array.isArray(rawNew) && rawNew.length > 0
        const isGlobal = !perm.object_id
        change.permissionObjectType =
          resolveObjectTypeToGerman(perm.object_type, {
            plural: isGlobal,
          }) || perm.object_type
        change.permissionLabel = resolvePermissionKeyLabel(perm.permission_key)
        change.permissionScope = perm.object_id || null
      }
    }

    return [change]
  })
}

async function resolveEventChangelog(changes) {
  const statusChange = changes.find((change) => change.key === 'status')

  if (statusChange) {
    statusChange.oldValue = await lookupStore.resolve(
      'eventStatus',
      statusChange.oldValue,
    )
    statusChange.newValue = await lookupStore.resolve(
      'eventStatus',
      statusChange.newValue,
    )
  }

  return changes
}

// Display formatting functions (passed to ChangelogChangesCell)
function formatFieldKey(str) {
  if (!str || typeof str !== 'string') return str

  const normalized = str.toLowerCase().replace(/_/g, '')

  if (FIELD_LABELS.value[normalized]) {
    return FIELD_LABELS.value[normalized]
  }

  return str
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function shortenMiddle(str, maxLength = 80, segmentLength = 30) {
  if (str === null || str === undefined) return ''
  if (typeof str !== 'string') str = String(str)
  if (str.length <= maxLength) return str

  const start = str.slice(0, segmentLength)
  const end = str.slice(-segmentLength)
  return `${start}[...]${end}`
}

function formatBoolean(val) {
  if (val === null || val === undefined || val === '') {
    return null
  }
  return typeof val === 'boolean'
    ? val
      ? t('common.yes')
      : t('common.no')
    : val
}

function formatDisplayValue(value) {
  // Empty values
  if (
    value === null ||
    value === undefined ||
    value === '' ||
    (Array.isArray(value) && value.length === 0)
  ) {
    return {
      isEmpty: true,
      value: t('components.changelog.noValue'),
    }
  }

  // Try parsing JSON string
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value)
      value = parsed
    } catch {
      // Keep original value
    }
  }

  // Array with key property
  if (
    Array.isArray(value) &&
    value.every((item) => typeof item === 'object' && 'key' in item)
  ) {
    return {
      isList: true,
      items: value.map((item) => formatFieldKey(item.key || '')),
    }
  }

  // Array with id property
  if (
    Array.isArray(value) &&
    value.every((item) => typeof item === 'object' && 'id' in item)
  ) {
    return {
      isList: true,
      items: value.map((item) => formatFieldKey(item.id || '')),
    }
  }

  // Array of strings
  if (Array.isArray(value) && value.every((item) => typeof item === 'string')) {
    return { isList: true, items: value }
  }

  // Boolean or simple value
  const formatted = formatBoolean(value)
  if (formatted === null) {
    return {
      isEmpty: true,
      value: t('components.changelog.noValue'),
    }
  }

  return { isSimple: true, value: formatted }
}

// Data fetching
async function fetchObjects() {
  try {
    dataLoading.value = true

    let response
    const params = {
      page: pagination.value.currentPage,
      limit: pagination.value.perPage,
      sort_by: pagination.value.sortColumnKey,
      sort_order: pagination.value.sortDirection,
      search_field: pagination.value.searchField,
      search_value: pagination.value.searchValue,
    }

    if (props.all === true) {
      response = await backend.changelog.list(params)
    } else {
      response = await backend.changelog.listByObject(
        props.objectType,
        props.objectId,
        params,
      )
    }

    for (const object of response.items) {
      // Parse changes
      object.parsedChanges = parseChanges(object)

      // Resolve username
      if (object.userId) {
        await resolveFieldFromLookup(object, [
          { from: 'userId', to: 'username', keyspace: 'users' },
        ])
      }

      // Resolve event status labels
      if (
        object.parsedChanges &&
        String(object.object).toLowerCase() === 'event'
      ) {
        await resolveEventChangelog(object.parsedChanges)
      }
    }

    objects.value = response.items
    totalCount.value = response.pageDetails.totalCount
  } catch (error) {
    console.error('Failed to load changelogs:', error)
  } finally {
    dataLoading.value = false
  }
}

// Event handlers
function handlePaginationChanged(newPage, newPerPage) {
  pagination.value.currentPage = newPage
  pagination.value.perPage = newPerPage
  fetchObjects()
}

function handleSortOrderChanged(direction, columnKey) {
  pagination.value.sortColumnKey = columnKey
  pagination.value.sortDirection = direction
  fetchObjects()
}

function handleSearch({ field, value }) {
  pagination.value.searchField = field
  pagination.value.searchValue = value
  pagination.value.currentPage = 1
  fetchObjects()
}

const searchBarFields = [
  {
    preset: 'createdById',
    key: 'userId',
    label: t('components.changelog.columns.changedBy'),
    operators: SearchOperators.EQUALS_ONLY_ONLY,
  },
]

onMounted(fetchObjects)
watch(() => props.objectId, fetchObjects)
</script>

<template>
  <SectionTitleLineWithButton
    :icon="mdiScriptTextOutline"
    title="Changelogs"
    :reload="fetchObjects"
  />

  <BaseTable
    object-model="changelog"
    :data="objects"
    :columns="columns"
    :loading="dataLoading"
    :search-bar-fields="searchBarFields"
    :search-bar-max-filters="1"
    :items-total="totalCount"
    :current-page="pagination.currentPage"
    :per-page="pagination.perPage"
    :sort-column-key="pagination.sortColumnKey"
    :sort-direction="pagination.sortDirection"
    created-column-key="timestamp"
    :created-column-label="t('components.changelog.columns.timestamp')"
    @pagination-changed="handlePaginationChanged"
    @sort-order-changed="handleSortOrderChanged"
    @search-triggered="handleSearch"
  >
    <template #cell-parsedChanges="{ value }">
      <ChangelogChangesCell
        :changes="value"
        :format-field-key="formatFieldKey"
        :format-display-value="formatDisplayValue"
        :shorten-middle="shortenMiddle"
      />
    </template>
  </BaseTable>
</template>
