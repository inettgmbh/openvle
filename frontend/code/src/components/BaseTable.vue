<script setup>
import {
  mdiArrowDown,
  mdiArrowUp,
  mdiCloseCircle,
  mdiEye,
  mdiPencil,
  mdiTrashCan,
} from '@mdi/js'
import { computed, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import PillTag from '@/components/PillTag.vue'
import TableCheckboxCell from '@/components/Tables/TableCheckboxCell.vue'
import TablePagination from '@/components/Tables/TablePagination.vue'
import TableSearchBar from '@/components/Tables/TableSearchBar.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { formatDate } from '@/utils/dataUtils.js'

/**
 * Returns standard column presets for common column types.
 * Presets are auto-applied based on column key, or explicitly via `preset` property.
 * Custom properties in the column definition will override preset defaults.
 *
 * @param {Function} t - i18n translation function
 * @returns {Object} Preset map keyed by column type.
 */
function getColumnPresets(t) {
  return {
    // Name column - text column for object names (flexible width)
    name: {
      label: t('components.baseTable.presets.name'),
      key: 'name',
    },
    // Description column - markdown-enabled text (flexible width)
    description: {
      label: t('components.baseTable.presets.description'),
      key: 'description',
      markdown: true,
    },
    // Symbol/Avatar column - displays user avatar based on ID
    symbol: {
      label: 'symbol',
      key: 'id',
      symbol: true,
      width: '70px',
    },
    // Email column
    email: {
      label: t('components.baseTable.presets.email'),
      key: 'email',
      width: '220px',
    },
    // Key column - identifier/slug field
    key: {
      label: t('components.baseTable.presets.key'),
      key: 'key',
      width: '150px',
    },
    // Protected/System column - boolean yes/no display
    protected: {
      label: t('components.baseTable.presets.protected'),
      key: 'protected',
      formatter: [t('common.yes'), t('common.no')],
      width: '100px',
    },
    // Username column
    username: {
      label: t('components.baseTable.presets.username'),
      key: 'username',
      width: '180px',
    },
    // Status column - typically uses color/icon, fixed width for pill tags
    status: {
      label: t('components.baseTable.presets.status'),
      key: 'status',
      width: '140px',
    },
  }
}

const props = defineProps({
  checkable: Boolean,
  symbol: Boolean,
  currentPage: {
    type: Number,
    default: 1,
  },
  data: {
    type: [Object],
    required: true,
  },
  itemsTotal: {
    type: [Number, String],
    default: 0,
  },
  perPage: {
    type: Number,
    default: 10,
  },
  sortColumnKey: {
    type: String,
    default: 'name',
  },
  sortDirection: {
    type: String,
    default: 'asc',
  },
  loading: {
    type: Boolean,
    default: true,
  },
  objectModel: {
    type: String,
    required: true,
  },
  columns: {
    type: Array,
    required: true,
  },
  buttons: {
    type: Array,
    default: null,
  },
  emitViewObject: {
    type: Boolean,
    default: false,
  },
  emitEditObject: {
    type: Boolean,
    default: false,
  },
  createdColumnKey: {
    type: String,
    default: 'createdAt',
  },
  createdColumnLabel: {
    type: String,
    default: null,
  },
  pagination: {
    type: Boolean,
    default: true,
  },
  createdColumnEnabled: {
    type: Boolean,
    default: true,
  },
  // TableSearchBar integration
  searchBarFields: {
    type: Array,
    default: () => [],
  },
  searchBarMaxFilters: {
    type: Number,
    default: 1,
  },
  searchBarPlaceholder: {
    type: String,
    default: null,
  },
  searchBarQueryKey: {
    type: String,
    default: null,
  },
  searchBarSyncQuery: {
    type: Boolean,
    default: true,
  },
  searchBarInitialFilters: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits([
  'editObject',
  'deleteObject',
  'paginationChanged',
  'searchTriggered',
  'sortOrderChanged',
  'viewObject',
  'checkedRowsChange',
])

const router = useRouter()
const { t } = useI18n()

const isActuallyLoading = ref(false)
const hasLoadedData = ref(false)
const lastRefresh = ref(null)
const searchBarRef = ref(null)
let loadingTimer

// Computed defaults with i18n fallbacks
const effectiveCreatedColumnLabel = computed(
  () => props.createdColumnLabel ?? t('common.createdAt'),
)
const effectiveSearchBarPlaceholder = computed(
  () => props.searchBarPlaceholder ?? t('common.filterPlaceholder'),
)
const showSearchBar = computed(() => props.searchBarFields.length > 0)
const effectiveSearchBarQueryKey = computed(
  () => props.searchBarQueryKey ?? 'filter',
)

// Track if we have loaded data at least once
const isInitialLoading = computed(
  () => isActuallyLoading.value && !hasLoadedData.value,
)
const isReloading = computed(
  () => isActuallyLoading.value && hasLoadedData.value,
)

function onSearchBarFiltersChanged({ filters, objectModel: model }) {
  if (filters.length === 0) {
    emit('searchTriggered', {
      field: '',
      value: '',
      objectModel: model,
    })
  } else {
    const firstFilter = filters[0]
    emit('searchTriggered', {
      field: firstFilter.field,
      value: firstFilter.value,
      operator: firstFilter.operator,
      filters: filters,
      objectModel: model,
    })
  }
}

const checkedRows = ref(new Set())
const checkedIds = ref(new Set())

// Preserve checked state across data reloads by matching item IDs
watch(
  () => props.data,
  (newData) => {
    if (checkedIds.value.size > 0 && newData) {
      checkedRows.value.clear()
      for (const item of newData) {
        if (checkedIds.value.has(item.id)) {
          checkedRows.value.add(item)
        }
      }
      // Remove IDs that no longer exist in the new data
      const newIds = new Set(newData.map((item) => item.id))
      for (const id of checkedIds.value) {
        if (!newIds.has(id)) checkedIds.value.delete(id)
      }
      emit('checkedRowsChange', Array.from(checkedRows.value))
    }
  },
)

const handlePagination = (page, perPage) => {
  emit('paginationChanged', page, perPage, props.objectModel)
}

const checked = (isChecked, obj) => {
  if (isChecked) {
    checkedRows.value.add(obj)
    checkedIds.value.add(obj.id)
  } else {
    checkedRows.value.delete(obj)
    checkedIds.value.delete(obj.id)
  }
  emit('checkedRowsChange', Array.from(checkedRows.value))
}

const uncheckAll = () => {
  checkedRows.value.clear()
  checkedIds.value.clear()
  emit('checkedRowsChange', [])
}

const sortColumn = (columnKey) => {
  const newDirection =
    props.sortColumnKey === columnKey && props.sortDirection === 'asc'
      ? 'desc'
      : 'asc'
  emit('sortOrderChanged', newDirection, columnKey, props.objectModel)
  return true
}

const handleView = (obj, event) => {
  if (emit && typeof emit === 'function' && props.emitViewObject) {
    emit('viewObject', obj, props.objectModel)
  } else {
    const path = `/${props.objectModel}/${obj.id}`
    // event.button === 1 is the middle mouse button (fires via auxclick on
    // <button> elements; click never fires for it in modern browsers).
    const openInNewTab = event?.metaKey || event?.ctrlKey || event?.button === 1
    if (openInNewTab) {
      window.open(`#${path}`, '_blank')
    } else {
      router.push({ path })
    }
  }
}

const handleEdit = (obj) => {
  if (emit && typeof emit === 'function' && props.emitEditObject) {
    emit('editObject', obj, props.objectModel)
  } else {
    router.push({ path: `/${props.objectModel}/${obj.id}/edit` })
  }
}

const handleDelete = (obj) => {
  emit('deleteObject', obj, props.objectModel)
}

const formatValue = (item, column) => {
  if (column.formatter) {
    const value = item[column.key]

    if (typeof column.formatter === 'function') {
      const formatted = column.formatter(value)
      return formatted
    }

    const formatted = value ? column.formatter[0] : column.formatter[1]
    return String(formatted)
  }

  const rawValue = item[column.key]
  return rawValue != null ? String(rawValue) : ''
}

const formatIcon = (item, column) => {
  if (typeof column.icon === 'function') {
    const formatted = column.icon(item[column.key])
    return formatted
  }
  return column.icon
}

const formatTooltip = (item, column) => {
  if (typeof column.tooltip === 'function') {
    const formatted = column.tooltip(item[column.key])
    return formatted
  }
  return column.tooltip
}

const normalizedColumns = computed(() => {
  const presets = getColumnPresets(t)
  return props.columns.map((col) => {
    // Auto-apply preset based on key if no explicit preset is set
    // Explicit preset takes precedence, then key-based preset, then empty
    const presetKey = col.preset ?? col.key
    const preset = presets[presetKey] ?? {}
    return {
      sortable: true,
      ...preset,
      ...col,
    }
  })
})

/**
 * Normalizes button config - converts string to object with defaults.
 */
const normalizeButton = (btn) => {
  if (typeof btn === 'string') {
    return {
      type: btn,
      visible: () => true,
      disabled: () => false,
      disabledTooltip: null,
    }
  }
  return {
    type: btn.type,
    visible: btn.visible ?? (() => true),
    disabled: btn.disabled ?? (() => false),
    disabledTooltip: btn.disabledTooltip ?? null,
  }
}

const normalizedButtons = computed(() => {
  if (!props.buttons) return []
  return props.buttons.map(normalizeButton)
})

const isButtonVisible = (buttonType, item) => {
  const btn = normalizedButtons.value.find((b) => b.type === buttonType)
  if (!btn) return false
  return typeof btn.visible === 'function' ? btn.visible(item) : btn.visible
}

const isButtonDisabled = (buttonType, item) => {
  const btn = normalizedButtons.value.find((b) => b.type === buttonType)
  if (!btn) return false
  return typeof btn.disabled === 'function' ? btn.disabled(item) : btn.disabled
}

const getButtonDisabledTooltip = (buttonType, item) => {
  const btn = normalizedButtons.value.find((b) => b.type === buttonType)
  if (!btn || !btn.disabledTooltip) return null
  return typeof btn.disabledTooltip === 'function'
    ? btn.disabledTooltip(item)
    : btn.disabledTooltip
}

const hasAnyButton = computed(() => {
  return normalizedButtons.value.some((b) =>
    ['view', 'edit', 'delete'].includes(b.type),
  )
})

const totalColumns = computed(() => {
  let columnCount = props.columns.length + 1
  if (hasAnyButton.value) {
    columnCount += 1
  }
  if (props.checkable) {
    columnCount += 1
  }
  return columnCount
})

watch(
  () => props.loading,
  (newVal) => {
    if (newVal) {
      isActuallyLoading.value = true
      clearTimeout(loadingTimer)
    } else {
      loadingTimer = setTimeout(() => {
        isActuallyLoading.value = false
        // Mark that we have loaded data at least once (regardless of data count)
        hasLoadedData.value = true
        // Track when data was last refreshed
        lastRefresh.value = new Date()
      }, 400)
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  clearTimeout(loadingTimer)
})

defineExpose({
  clearSearchBar: () => searchBarRef.value?.clearAll(),
  focusSearchBar: () => searchBarRef.value?.focus(),
  searchBarRef,
  checkedRows,
  clearCheckedRows: () => {
    checkedRows.value.clear()
    checkedIds.value.clear()
  },
})
</script>

<template>
  <div>
    <!-- Integrated TableSearchBar -->
    <TableSearchBar
      v-if="showSearchBar"
      ref="searchBarRef"
      :fields="searchBarFields"
      :max-filters="searchBarMaxFilters"
      :object-model="objectModel"
      :placeholder="effectiveSearchBarPlaceholder"
      :sync-query="searchBarSyncQuery"
      :query-key="effectiveSearchBarQueryKey"
      :initial-filters="searchBarInitialFilters"
      class="px-4 mt-4 mb-10"
      @filters-changed="onSearchBarFiltersChanged"
    />

    <div class="relative">
      <div
        v-if="checkedRows.size"
        class="flex items-center p-3 bg-gray-100/50 dark:bg-slate-800"
      >
        <div class="flex-1 flex flex-wrap gap-2">
          <span
            v-for="row in Array.from(checkedRows)"
            :key="row.id"
            class="inline-block px-2 py-1 rounded-sm text-sm bg-gray-100 dark:bg-slate-700"
          >
            {{ row[normalizedColumns[0]?.key] || row.name || row.id }}
          </span>
        </div>

        <button
          type="button"
          class="ml-3 flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
          @click="uncheckAll"
        >
          <BaseIcon :path="mdiCloseCircle" w="w-5" h="h-5" />
        </button>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr>
              <!-- Table Header: Checkable -->
              <th v-if="checkable" class="w-10" />

              <!-- Table Header: Symbol -->
              <th v-if="symbol" class="w-16" />

              <!-- Table Header: Data columns -->
              <th
                v-for="column in normalizedColumns.filter(
                  (column) => !column.symbol,
                )"
                :key="column.key"
                class="cursor-pointer select-none whitespace-nowrap relative"
                :class="{
                  sorted: sortColumnKey === (column.sortKey || column.key),
                  asc: sortDirection === 'asc',
                  desc: sortDirection === 'desc',
                  'h-16': column.filters,
                }"
                :style="
                  column.width
                    ? { width: column.width, maxWidth: column.width }
                    : undefined
                "
              >
                <div class="inline-flex items-center gap-1">
                  <span>{{ column.label }}</span>

                  <div class="flex flex-col sm:flex-row sm:gap-0.5">
                    <!-- Sort asc icon -->
                    <BaseIcon
                      v-if="column.sortable !== false"
                      w=""
                      h=""
                      fill="currentColor"
                      :path="mdiArrowUp"
                      :class="[
                        'inline-block',
                        sortColumnKey === (column.sortKey || column.key) &&
                        sortDirection === 'asc'
                          ? 'text-black dark:text-white font-bold'
                          : 'text-gray-400',
                      ]"
                      @click="sortColumn(column.sortKey || column.key)"
                    />

                    <!-- Sort desc icon -->
                    <BaseIcon
                      v-if="column.sortable !== false"
                      w=""
                      h=""
                      fill="currentColor"
                      :path="mdiArrowDown"
                      :class="[
                        'inline-block',
                        sortColumnKey === (column.sortKey || column.key) &&
                        sortDirection === 'desc'
                          ? 'text-black dark:text-white font-bold'
                          : 'text-gray-400',
                      ]"
                      @click="sortColumn(column.sortKey || column.key)"
                    />
                  </div>
                </div>
              </th>

              <!-- Table Header: CreatedAt column -->
              <th
                v-if="props.createdColumnEnabled"
                class="whitespace-nowrap cursor-pointer select-none lg:text-right"
                style="width: 140px"
                :class="{
                  sorted: sortColumnKey === createdColumnKey,
                  asc: sortDirection === 'asc',
                  desc: sortDirection === 'desc',
                }"
                @click="sortColumn(createdColumnKey)"
              >
                <div
                  class="inline-flex items-start sm:items-center flex-col sm:flex-row gap-0.5 sm:gap-1"
                >
                  <span>{{ effectiveCreatedColumnLabel }}</span>

                  <div class="flex flex-col sm:flex-row sm:gap-0.5">
                    <BaseIcon
                      w=""
                      h=""
                      iconsize="24"
                      fill="currentColor"
                      viewBox="0 0 24 24"
                      :path="mdiArrowUp"
                      :class="[
                        'inline-block',
                        sortColumnKey === createdColumnKey &&
                        sortDirection === 'asc'
                          ? 'text-black dark:text-white font-bold'
                          : 'text-gray-400',
                      ]"
                    />

                    <BaseIcon
                      w=""
                      h=""
                      fill="currentColor"
                      :path="mdiArrowDown"
                      :class="[
                        'inline-block',
                        sortColumnKey === createdColumnKey &&
                        sortDirection === 'desc'
                          ? 'text-black dark:text-white font-bold'
                          : 'text-gray-400',
                      ]"
                    />
                  </div>
                </div>
              </th>

              <!-- Table Header: Buttons column -->
              <th
                v-if="hasAnyButton"
                class="lg:text-right lg:pl-4"
                :style="{
                  width:
                    normalizedButtons.filter((b) =>
                      ['view', 'edit', 'delete'].includes(b.type),
                    ).length *
                      36 +
                    8 +
                    'px',
                }"
              />
            </tr>
          </thead>

          <!-- Table Body: Initial loading (skeleton) -->
          <tbody v-if="isInitialLoading" key="loading">
            <tr v-for="i in perPage >= 5 ? 5 : perPage" :key="'skeleton-' + i">
              <td v-if="checkable" />

              <td v-for="column in normalizedColumns" :key="column.key">
                <div
                  v-if="column.symbol"
                  class="rounded-full bg-gray-200 dark:bg-slate-700 h-6 w-6 mx-auto animate-pulse"
                />

                <div
                  v-else-if="column.color"
                  class="rounded-full h-4 w-16 bg-gray-200 dark:bg-slate-700 animate-pulse"
                />
                <!-- default fallback -->
                <div
                  v-else
                  class="h-4 w-24 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"
                />
              </td>

              <td v-if="props.createdColumnEnabled">
                <div
                  class="h-4 w-20 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"
                />
              </td>

              <td v-if="hasAnyButton">
                <div class="flex justify-end gap-1">
                  <div
                    v-for="j in normalizedButtons.length"
                    :key="j"
                    class="h-6 w-6 bg-gray-200 dark:bg-slate-700 rounded-full animate-pulse"
                  />
                </div>
              </td>
            </tr>
          </tbody>

          <!-- Table Body: No data found / empty table -->
          <tbody v-else-if="!itemsTotal && !isReloading" key="empty">
            <tr>
              <td :colspan="totalColumns" class="text-center font-bold">
                {{ $t('common.noData') }}
              </td>
            </tr>
          </tbody>

          <!-- Table Body: Data found (with optional reload overlay) -->
          <tbody v-else key="data" class="relative">
            <tr v-for="item in data" :key="item.id">
              <!-- Table Column: Checkable -->
              <TableCheckboxCell
                v-if="checkable"
                :key="`check-${item.id}`"
                :model-value="checkedIds.has(item.id)"
                @checked="checked($event, item)"
              />

              <td
                v-for="column in normalizedColumns"
                :key="column.key"
                :data-label="column.label"
                :class="{ 'text-center': column.color }"
                :style="{ '--col-width': column.width || '250px' }"
              >
                <!-- Table Column: Custom slot for column (highest priority) -->
                <slot
                  v-if="$slots[`cell-${column.key}`]"
                  :name="`cell-${column.key}`"
                  :item="item"
                  :column="column"
                  :value="item[column.key]"
                />

                <!-- Table Column: Color and no icon: Pilltag with color and w/o icon -->
                <PillTag
                  v-else-if="column.color && !column.icon"
                  v-tooltip="formatTooltip(item, column)"
                  :label="formatValue(item, column)"
                  :color="column.color(item[column.key])"
                  :disabled="true"
                  :class="column.class"
                />

                <!-- Table Column: Color and icon: Pilltag with color and icon -->
                <PillTag
                  v-else-if="column.color && column.icon"
                  v-tooltip="formatTooltip(item, column)"
                  :label="formatValue(item, column)"
                  :icon="formatIcon(item, column)"
                  :color="column.color(item[column.key])"
                  :disabled="true"
                  :class="column.class"
                />

                <!-- Table Column: Symbol: UserAvatar with key as seed -->
                <UserAvatar
                  v-else-if="column.symbol"
                  :userid="item[column.key]"
                  class="w-24 h-24 mx-auto lg:w-6 lg:h-6"
                  :class="column.class"
                />

                <!-- Table Column: (Only) Formatter: Use custom formatter -->
                <span v-else-if="column.formatter" :class="column.class">
                  {{ formatValue(item, column) }}
                </span>

                <!-- Table Column: Markdown: Render content as markdown -->
                <span
                  v-else-if="column.markdown"
                  class="markdown-cell"
                  :class="column.class"
                >
                  <MarkdownRenderer
                    class="truncate-lines"
                    style="--lines: 2"
                    :class="column.class"
                    :markdown-text="item[column.key]"
                  />
                </span>

                <!-- Table Column: Else: Render content as it is -->
                <span v-else :class="column.class">
                  {{ formatValue(item, column) }}
                </span>
              </td>

              <!-- Table Column: CreatedAt: CreatedAt column -->
              <td
                v-if="props.createdColumnEnabled"
                :data-label="effectiveCreatedColumnLabel"
                class="whitespace-nowrap lg:text-right"
              >
                <small
                  class="text-gray-500 dark:text-slate-400"
                  :title="item[createdColumnKey]"
                >
                  {{ formatDate(item[createdColumnKey]) }}
                </small>
              </td>

              <!-- Table Column: Buttons -->
              <td
                v-if="hasAnyButton"
                class="before:hidden whitespace-nowrap lg:text-right lg:pl-4 lg:align-middle"
              >
                <BaseButtons type="justify-start lg:justify-end" no-wrap>
                  <!-- Table Button: View -->
                  <BaseButton
                    v-if="isButtonVisible('view', item)"
                    v-tooltip="
                      isButtonDisabled('view', item)
                        ? getButtonDisabledTooltip('view', item)
                        : null
                    "
                    color="info"
                    :icon="mdiEye"
                    :label="$t('common.view')"
                    class="btn-label-mobile"
                    small
                    :disabled="isButtonDisabled('view', item)"
                    @click="handleView(item, $event)"
                    @auxclick.middle="handleView(item, $event)"
                  />

                  <!-- Table Button: Edit -->
                  <BaseButton
                    v-if="isButtonVisible('edit', item)"
                    v-tooltip="
                      isButtonDisabled('edit', item)
                        ? getButtonDisabledTooltip('edit', item)
                        : null
                    "
                    color="contrast"
                    :icon="mdiPencil"
                    :label="$t('common.edit')"
                    class="btn-label-mobile"
                    small
                    :disabled="isButtonDisabled('edit', item)"
                    @click="handleEdit(item)"
                  />

                  <!-- Table Button: Delete -->
                  <BaseButton
                    v-if="isButtonVisible('delete', item)"
                    v-tooltip="
                      isButtonDisabled('delete', item)
                        ? getButtonDisabledTooltip('delete', item)
                        : null
                    "
                    color="danger"
                    :icon="mdiTrashCan"
                    :label="$t('common.delete')"
                    class="btn-label-mobile"
                    small
                    :disabled="isButtonDisabled('delete', item)"
                    @click="handleDelete(item)"
                  />
                </BaseButtons>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Reload overlay -->
      <transition name="fade-overlay">
        <div
          v-if="isReloading"
          class="absolute inset-0 bg-white/60 dark:bg-slate-900/60 backdrop-blur-[1px] flex items-center justify-center z-10 rounded-lg"
        >
          <div
            class="flex items-center gap-3 px-4 py-2 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700"
          >
            <div
              class="w-5 h-5 border-2 border-gray-300 dark:border-slate-500 border-t-blue-500 dark:border-t-blue-400 rounded-full animate-spin"
            />

            <span class="text-sm text-gray-600 dark:text-slate-300">{{
              t('components.baseTable.refreshing')
            }}</span>
          </div>
        </div>
      </transition>

      <TablePagination
        v-if="props.pagination"
        :current-page="currentPage"
        :items-total="itemsTotal"
        :per-page="perPage"
        :last-refresh="lastRefresh"
        @pagination-changed="handlePagination"
      />

      <div
        v-if="!props.pagination"
        class="p-3 lg:px-6 border-t border-gray-100 dark:border-slate-800"
      />
    </div>
  </div>
</template>

<style scoped>
/* Overlay fade transition */
.fade-overlay-enter-active,
.fade-overlay-leave-active {
  transition: opacity 0.2s ease;
}
.fade-overlay-enter-from,
.fade-overlay-leave-to {
  opacity: 0;
}

/* Show label on mobile, hide on larger screens (only the label span, not the icon span) */
@media (min-width: 1024px) {
  .btn-label-mobile :deep(span + span) {
    display: none;
  }
}

/* Truncate cell content that overflows - only on desktop */
@media (min-width: 1024px) {
  td {
    max-width: var(--col-width, 250px);
  }

  td > span:not(.markdown-cell) {
    display: block;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    padding-right: 1rem;
  }

  /* Markdown cells need white-space: normal for multi-line truncation */
  td > span.markdown-cell {
    display: block;
    overflow: hidden;
    padding-right: 1rem;
  }
}
</style>
