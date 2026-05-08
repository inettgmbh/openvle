<script setup>
import {
  mdiCheck,
  mdiChevronRight,
  mdiClose,
  mdiLoading,
  mdiMagnify,
} from '@mdi/js'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseIcon from '@/components/BaseIcon.vue'
import { useSearchLookup } from '@/components/Tables/composables/useSearchLookup'
import { useSearchQuerySync } from '@/components/Tables/composables/useSearchQuerySync'
import { useSearchState } from '@/components/Tables/composables/useSearchState'
import {
  DEFAULT_FIELD_ICON,
  resolveFieldPresets,
} from '@/components/Tables/searchFieldPresets'

const props = defineProps({
  fields: {
    type: Array,
    required: true,
  },
  maxFilters: {
    type: Number,
    default: 1,
  },
  objectModel: {
    type: String,
    default: null,
  },
  placeholder: {
    type: String,
    default: null,
  },
  initialFilters: {
    type: Array,
    default: () => [],
  },
  syncQuery: {
    type: Boolean,
    default: true,
  },
  queryKey: {
    type: String,
    default: 'filter',
  },
})

const emit = defineEmits(['filtersChanged'])
const { t } = useI18n()

// Computed: effective placeholder with i18n fallback
const effectivePlaceholder = computed(
  () => props.placeholder ?? t('common.filterPlaceholder'),
)

// Refs
const rootEl = ref(null)
const inputEl = ref(null)

// Active filters state
const activeFilters = ref([])

// Computed: resolve presets
const resolvedFields = computed(() => resolveFieldPresets(props.fields))

// Computed: available fields (hide already-used when multiple filters allowed)
const availableFields = computed(() => {
  if (props.maxFilters === 1) return resolvedFields.value
  const usedKeys = new Set(activeFilters.value.map((f) => f.field))
  return resolvedFields.value.filter((f) => !usedKeys.has(f.key))
})

// Computed: fallback to "name" field when no dropdown items match in field phase
const nameFieldFallback = computed(() => {
  if (phase.value !== 'field') return null
  if (!inputValue.value.trim()) return null
  if (dropdownItems.value.length > 0) return null
  return availableFields.value.find((f) => f.key === 'name') || null
})

// Computed: whether adding more filters is possible
const canAddMore = computed(() => {
  const withinLimit =
    props.maxFilters === 0 || activeFilters.value.length < props.maxFilters
  return withinLimit && availableFields.value.length > 0
})

// Initialize lookup composable
const {
  lookupResults,
  lookupLoading,
  lookupMinChars,
  showLookupMinCharsHint,
  showLookupNoResults,
  performLookup,
  resetLookup,
} = useSearchLookup({
  selectedField: computed(() => selectedField.value),
  inputValue: computed(() => inputValue.value),
  phase: computed(() => phase.value),
})

// Initialize state composable
const {
  phase,
  selectedField,
  selectedOperator,
  inputValue,
  highlightedIndex,
  isDateTimeField,
  dateTimeInputType,
  resetInput,
  enterFieldPhase,
  selectField,
  selectOperator,
  confirmFreetext,
  confirmDateTime,
  selectValue,
  goBackOnePhase,
} = useSearchState({
  getResolvedFields: () => resolvedFields.value,
  activeFilters,
  canAddMore,
  maxFilters: props.maxFilters,
  inputEl,
  onFilterAdded: emitFilters,
  resetLookup,
})

// Initialize query sync composable
const { syncFiltersToQuery, initializeFilters, setupQueryWatcher } =
  useSearchQuerySync({
    activeFilters,
    getResolvedFields: () => resolvedFields.value,
    syncQuery: props.syncQuery,
    queryKey: props.queryKey,
    initialFilters: props.initialFilters,
    onFiltersRestored: emitFilters,
  })

// Computed: dropdown items based on current phase
const dropdownItems = computed(() => {
  if (phase.value === 'field') {
    const query = inputValue.value.toLowerCase()
    return availableFields.value
      .filter((f) => !query || f.label.toLowerCase().includes(query))
      .sort((a, b) => a.label.localeCompare(b.label, 'de'))
      .map((f) => ({
        key: f.key,
        label: f.label,
        icon: f.icon || DEFAULT_FIELD_ICON,
        raw: f,
      }))
  }
  if (phase.value === 'operator') {
    return (selectedField.value?.operators || []).map((op) => ({
      key: op.key,
      label: op.label,
      icon: op.icon || null,
      raw: op,
    }))
  }
  if (phase.value === 'value') {
    // Lookup fields: show lookup results
    if (selectedField.value?.type === 'lookup') {
      return lookupResults.value
    }
    // Options fields: filter options
    if (selectedField.value?.options) {
      const query = inputValue.value.toLowerCase()
      return selectedField.value.options
        .filter((opt) => !query || opt.label.toLowerCase().includes(query))
        .map((opt) => ({
          key: opt.value,
          label: opt.label,
          icon: opt.icon || null,
          color: opt.color || null,
          raw: opt,
        }))
    }
  }
  return []
})

const showDropdown = computed(() => {
  if (phase.value === 'field' || phase.value === 'operator') return true
  if (phase.value === 'value') {
    // Show dropdown for options fields
    if (selectedField.value?.options) return true
    // Show dropdown for lookup fields (when loading, has results, hint, or no results)
    if (selectedField.value?.type === 'lookup') {
      return (
        lookupLoading.value ||
        lookupResults.value.length > 0 ||
        showLookupMinCharsHint.value ||
        showLookupNoResults.value
      )
    }
  }
  return false
})

// Methods
function emitFilters() {
  emit('filtersChanged', {
    filters: activeFilters.value.map((f) => ({
      field: f.field,
      operator: f.operator,
      value: f.value,
    })),
    objectModel: props.objectModel,
  })
  syncFiltersToQuery()
}

function handleDropdownSelect(item) {
  if (phase.value === 'field') {
    selectField(item.raw)
  } else if (phase.value === 'operator') {
    selectOperator(item.raw)
  } else if (phase.value === 'value') {
    selectValue(item.key, item.label)
  }
}

function onInputFocus() {
  if (phase.value === 'idle' && canAddMore.value) {
    enterFieldPhase()
  }
}

function onKeydown(e) {
  const items = dropdownItems.value

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (items.length > 0) {
      highlightedIndex.value = (highlightedIndex.value + 1) % items.length
    }
    return
  }

  if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (items.length > 0) {
      highlightedIndex.value =
        (highlightedIndex.value - 1 + items.length) % items.length
    }
    return
  }

  if (e.key === 'Enter') {
    e.preventDefault()
    if (highlightedIndex.value >= 0 && items[highlightedIndex.value]) {
      handleDropdownSelect(items[highlightedIndex.value])
    } else if (phase.value === 'field' && nameFieldFallback.value) {
      // No field matches typed text, but "name" field exists — use it as fallback
      const typedValue = inputValue.value.trim()
      selectField(nameFieldFallback.value)
      // selectField resets inputValue — restore typed text and submit
      nextTick(() => {
        inputValue.value = typedValue
        confirmFreetext()
      })
    } else if (phase.value === 'value') {
      // Lookup fields: auto-select if exactly one result, otherwise block
      if (selectedField.value?.type === 'lookup') {
        if (items.length === 1) {
          handleDropdownSelect(items[0])
        }
      } else if (!selectedField.value?.options) {
        confirmFreetext()
      }
    }
    return
  }

  if (e.key === 'Escape') {
    e.preventDefault()
    resetInput()
    return
  }

  if (e.key === 'Backspace' && inputValue.value === '') {
    e.preventDefault()
    if (phase.value === 'value' || phase.value === 'operator') {
      goBackOnePhase()
    } else if (phase.value === 'field' || phase.value === 'idle') {
      // Remove last chip
      if (activeFilters.value.length > 0) {
        activeFilters.value.pop()
        emitFilters()
        if (phase.value === 'idle') {
          phase.value = 'field'
        }
      }
    }
    return
  }
}

function onInput() {
  highlightedIndex.value = -1
  // Typing in idle phase should open field selection
  if (phase.value === 'idle' && canAddMore.value) {
    phase.value = 'field'
  }
  // Trigger lookup search when in value phase for lookup fields
  if (phase.value === 'value' && selectedField.value?.type === 'lookup') {
    performLookup(inputValue.value)
  }
}

function removeFilter(index) {
  activeFilters.value.splice(index, 1)
  emitFilters()
}

function clearAll() {
  activeFilters.value = []
  resetInput()
  emitFilters()
}

function focus() {
  inputEl.value?.focus()
}

// Click outside
function handleClickOutside(event) {
  if (!rootEl.value) return
  if (!rootEl.value.contains(event.target)) {
    resetInput()
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleClickOutside, { capture: true })
  setupQueryWatcher()
  initializeFilters()
})

onBeforeUnmount(() =>
  document.removeEventListener('click', handleClickOutside, { capture: true }),
)

defineExpose({ clearAll, focus })
</script>

<template>
  <div ref="rootEl" class="relative mb-4">
    <!-- Search bar container -->
    <div
      class="flex items-center gap-2 border rounded-lg px-3 py-2 bg-white dark:bg-slate-800 border-gray-300 dark:border-slate-600 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-colors duration-150"
      @click="onInputFocus"
    >
      <!-- Wrapping content area -->
      <div class="flex-1 flex flex-wrap items-center gap-1.5">
        <!-- Active filter chips -->
        <span
          v-for="(filter, index) in activeFilters"
          :key="`${filter.field}-${index}`"
          class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-sm bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300"
        >
          <BaseIcon
            :path="filter.fieldIcon"
            class="w-3.5 h-3.5"
            fill="currentColor"
          />

          <span>{{ filter.fieldLabel }}</span>

          <BaseIcon
            v-if="filter.operatorIcon"
            :path="filter.operatorIcon"
            class="w-3.5 h-3.5"
            fill="currentColor"
          />

          <span v-if="filter.displayValue">{{
            filter.isFreetext
              ? `"${filter.displayValue}"${filter.suffix ? ` ${filter.suffix}` : ''}`
              : filter.displayValue
          }}</span>

          <button
            type="button"
            class="ml-0.5 hover:text-blue-600 dark:hover:text-blue-100 transition-colors"
            @click.stop="removeFilter(index)"
          >
            <BaseIcon
              :path="mdiClose"
              class="w-3.5 h-3.5"
              fill="currentColor"
            />
          </button>
        </span>

        <!-- Breadcrumb during input -->
        <span
          v-if="selectedField"
          class="inline-flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400"
        >
          <BaseIcon
            :path="selectedField.icon || DEFAULT_FIELD_ICON"
            class="w-4 h-4"
            fill="currentColor"
          />

          <span>{{ selectedField.label }}</span>

          <BaseIcon
            :path="mdiChevronRight"
            class="w-3.5 h-3.5"
            fill="currentColor"
          />

          <template v-if="selectedOperator">
            <BaseIcon
              v-if="selectedOperator.icon"
              :path="selectedOperator.icon"
              class="w-4 h-4"
              fill="currentColor"
            />

            <BaseIcon
              :path="mdiChevronRight"
              class="w-3.5 h-3.5"
              fill="currentColor"
            />
          </template>
        </span>

        <!-- Text input (hidden when filter limit reached and idle, or when date/time picker is shown) -->
        <input
          v-if="
            (canAddMore || phase !== 'idle') &&
            !(phase === 'value' && isDateTimeField)
          "
          ref="inputEl"
          v-model="inputValue"
          type="text"
          autocomplete="off"
          autocorrect="off"
          autocapitalize="off"
          spellcheck="false"
          :placeholder="
            phase === 'idle' || phase === 'field'
              ? effectivePlaceholder
              : phase === 'operator'
                ? t('components.tableSearchBar.selectOperator')
                : selectedField?.type === 'lookup'
                  ? t('components.tableSearchBar.searchMinChars', {
                      min: lookupMinChars,
                    })
                  : selectedField?.options
                    ? t('components.tableSearchBar.selectValue')
                    : selectedField?.suffix
                      ? `${t('components.tableSearchBar.enterValue')} (${selectedField.suffix})`
                      : t('components.tableSearchBar.enterValue')
          "
          class="flex-1 min-w-[120px] bg-transparent border-0 outline-none text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
          @focus="onInputFocus"
          @keydown="onKeydown"
          @input="onInput"
        />

        <!-- Date/Time picker input -->
        <input
          v-if="phase === 'value' && isDateTimeField"
          ref="inputEl"
          v-model="inputValue"
          :type="dateTimeInputType"
          autocomplete="off"
          autocorrect="off"
          autocapitalize="off"
          spellcheck="false"
          class="flex-1 min-w-[140px] bg-transparent border-0 outline-none text-sm text-gray-900 dark:text-gray-100"
          @keydown.enter.prevent="confirmDateTime"
          @keydown.escape.prevent="resetInput"
        />

        <!-- Confirm button for date/time picker -->
        <button
          v-if="phase === 'value' && isDateTimeField && inputValue"
          type="button"
          class="p-1 rounded hover:bg-blue-100 dark:hover:bg-blue-900/40 text-blue-600 dark:text-blue-400 transition-colors"
          :title="$t('components.tableSearchBar.applyEnter')"
          @click="confirmDateTime"
        >
          <BaseIcon :path="mdiCheck" class="w-4 h-4" fill="currentColor" />
        </button>

        <!-- Loading spinner for lookup -->
        <BaseIcon
          v-if="lookupLoading"
          :path="mdiLoading"
          class="w-4 h-4 text-blue-500 animate-spin shrink-0"
          fill="currentColor"
        />

        <!-- Hint when no more filters can be added -->
        <span
          v-if="!canAddMore && phase === 'idle'"
          class="flex-1 text-sm text-gray-400 dark:text-gray-500 italic"
        >
          {{
            availableFields.length === 0
              ? t('components.tableSearchBar.allFiltersUsed')
              : t('components.tableSearchBar.maxFiltersReached')
          }}
        </span>
      </div>

      <!-- Icons container (vertically centered) -->
      <div class="flex items-center gap-1 shrink-0">
        <!-- Clear all filters button -->
        <button
          v-if="activeFilters.length > 0"
          type="button"
          class="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/40 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
          :title="$t('components.tableSearchBar.removeAllFilters')"
          @click.stop="clearAll"
        >
          <BaseIcon :path="mdiClose" class="w-4 h-4" fill="currentColor" />
        </button>

        <!-- Search icon -->
        <BaseIcon
          :path="mdiMagnify"
          class="w-5 h-5 text-gray-400 dark:text-gray-500"
          fill="currentColor"
        />
      </div>
    </div>

    <!-- Dropdown -->
    <transition
      enter-active-class="transition ease-out duration-150"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <ul
        v-if="showDropdown"
        class="absolute z-50 mt-1 w-full max-h-[40vh] overflow-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-lg p-1"
        role="listbox"
      >
        <!-- Lookup: min chars hint -->
        <li
          v-if="showLookupMinCharsHint"
          class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400 italic"
        >
          {{
            t('components.tableSearchBar.minCharsHint', {
              min: lookupMinChars,
            })
          }}
        </li>

        <!-- Lookup: loading state -->
        <li
          v-else-if="lookupLoading"
          class="flex items-center gap-2 px-3 py-2 text-sm text-gray-500 dark:text-gray-400"
        >
          <BaseIcon
            :path="mdiLoading"
            class="w-4 h-4 animate-spin"
            fill="currentColor"
          />

          <span>{{ t('components.tableSearchBar.searching') }}</span>
        </li>

        <!-- Lookup: no results -->
        <li
          v-else-if="
            selectedField?.type === 'lookup' &&
            !lookupLoading &&
            dropdownItems.length === 0 &&
            inputValue.length >= lookupMinChars
          "
          class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400 italic"
        >
          {{ t('common.noResults') }}
        </li>

        <!-- Name fallback hint when no field matches -->
        <li
          v-if="nameFieldFallback"
          class="flex items-center gap-2 cursor-pointer rounded-md px-3 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
          @click.stop="
            () => {
              const typedValue = inputValue.trim()
              selectField(nameFieldFallback)
              nextTick(() => {
                inputValue = typedValue
                confirmFreetext()
              })
            }
          "
        >
          <BaseIcon
            :path="mdiMagnify"
            class="w-4 h-4 shrink-0"
            fill="currentColor"
          />

          <span>{{
            t('components.tableSearchBar.searchByName', {
              query: inputValue.trim(),
            })
          }}</span>
        </li>

        <!-- Regular dropdown items -->
        <template v-else>
          <li
            v-for="(item, index) in dropdownItems"
            :key="item.key"
            role="option"
            :aria-selected="highlightedIndex === index"
            class="flex items-center gap-2 cursor-pointer rounded-md px-3 py-2 text-sm transition-colors duration-150"
            :class="
              highlightedIndex === index
                ? 'bg-blue-100 dark:bg-blue-600 text-blue-900 dark:text-white'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700'
            "
            @click.stop="handleDropdownSelect(item)"
            @mouseenter="highlightedIndex = index"
          >
            <!-- Optional icon (for status options etc.) -->
            <BaseIcon
              v-if="item.icon"
              :path="item.icon"
              class="w-4 h-4 shrink-0"
              :fill="item.color || 'currentColor'"
            />

            <!-- Color dot (when color but no icon) -->
            <span
              v-else-if="item.color"
              class="w-2.5 h-2.5 rounded-full shrink-0"
              :style="{ backgroundColor: item.color }"
            />

            <span>{{ item.label }}</span>
          </li>
        </template>
      </ul>
    </transition>
  </div>
</template>
