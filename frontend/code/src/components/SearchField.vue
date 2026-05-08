<script setup>
import debounce from 'lodash/debounce'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { useStyleStore } from '@/stores/style.js'

const { t } = useI18n()
const styleStore = useStyleStore()

const props = defineProps({
  maxEntries: {
    type: Number,
    default: 25,
  },
  fetchData: {
    type: Function,
    required: true,
  },
  returnAttribute: {
    type: String,
    default: 'id',
  },
  placeholder: {
    type: String,
    default: null,
  },
  required: {
    type: Boolean,
    default: false,
  },
  autocomplete: {
    type: Boolean,
    default: false,
  },
  autofocus: {
    type: Boolean,
    default: false,
  },
  icon: {
    type: String,
    default: null,
  },
  id: {
    type: String,
    required: true,
  },
  ariaDescribedby: {
    type: String,
    required: false,
    default: null,
  },
  labelAttribute: {
    type: String,
    default: 'name',
  },
  allowCustomEntry: {
    type: Boolean,
    default: false,
  },
  formatter: {
    type: Function,
    default: (val) => val,
  },
  maxlength: {
    type: Number,
    default: null,
  },
  borders: {
    type: String,
    default: 'all',
    validator: (value) =>
      ['all', 'none', 'right', 'left', 'top/bottom'].includes(value),
  },
})

const emit = defineEmits(['select'])

const activeIndex = ref(-1)
const entries = ref([])
const hasFocus = ref(false)
const hoveredIndex = ref(null)
const inputRef = ref(null)
const isClickingEntry = ref(false)
const isLoading = ref(false)
const isProgrammaticInput = ref(false)
const isUsingKeyboard = ref(false)
const searchQuery = ref('')
const selectedEntryId = ref(null)
const totalCount = ref(0)

const fetchEntries = async (query) => {
  try {
    const result = await props.fetchData(query)
    entries.value = result.items
    totalCount.value = result.pageDetails.totalCount
  } catch (error) {
    console.error('Error fetching data:', error)
  } finally {
    isLoading.value = false
  }
}

const debouncedFetchEntries = debounce((query) => {
  fetchEntries(query)
}, 300)

const onInput = () => {
  if (searchQuery.value.length >= 3) {
    isLoading.value = true
    debouncedFetchEntries(searchQuery.value)
  } else {
    isLoading.value = false
    entries.value = []
  }

  if (selectedEntryId.value) {
    selectedEntryId.value = null
    emit('select', null)
  }
  activeIndex.value = -1
}

const onKeyDown = (e) => {
  if (!displayedEntries.value.length && !props.allowCustomEntry) return

  if (e.altKey && e.key === 'ArrowDown') {
    e.preventDefault()
    isUsingKeyboard.value = true
    hoveredIndex.value = null
    activeIndex.value = displayedEntries.value.length - 1
    scrollActiveIntoView()
    return
  }

  if (e.altKey && e.key === 'ArrowUp') {
    e.preventDefault()
    isUsingKeyboard.value = true
    hoveredIndex.value = null
    activeIndex.value = 0
    scrollActiveIntoView()
    return
  }

  isUsingKeyboard.value = true
  hoveredIndex.value = null
  let startIndex = activeIndex.value

  if (startIndex === -1 && hoveredIndex.value !== null) {
    startIndex = hoveredIndex.value
  }

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = (startIndex + 1) % displayedEntries.value.length
    scrollActiveIntoView()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value =
      (startIndex - 1 + displayedEntries.value.length) %
      displayedEntries.value.length
    scrollActiveIntoView()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (currentActiveIndex.value >= 0) {
      selectEntry(displayedEntries.value[currentActiveIndex.value])
    } else if (props.allowCustomEntry && searchQuery.value.length >= 1) {
      selectOrCreateEntry()
    }
  } else if (e.key === 'Escape') {
    e.preventDefault()
    resetSearch()
  }
}

const scrollActiveIntoView = () => {
  const el = document.querySelector('.search-component li.active-entry')
  el?.scrollIntoView({ block: 'nearest' })
}

const selectEntry = (entry) => {
  isClickingEntry.value = true
  const returnValue = entry[props.returnAttribute]
  emit('select', returnValue)
  selectedEntryId.value = entry.id
  isProgrammaticInput.value = true
  searchQuery.value = entry[props.labelAttribute]
  entries.value = []
  activeIndex.value = -1
  setTimeout(() => {
    isClickingEntry.value = false
  }, 150)
}

const resetSearch = () => {
  searchQuery.value = ''
  entries.value = []
  totalCount.value = 0
  selectedEntryId.value = null
  activeIndex.value = -1
  hoveredIndex.value = -1 // fixme: reset on close not working (parent bug?)
}

const selectOrCreateEntry = () => {
  const formattedInput = props.formatter(searchQuery.value)
  const match = entries.value.find(
    (entry) => props.formatter(entry[props.labelAttribute]) === formattedInput,
  )

  const selected = match ? match[props.returnAttribute] : formattedInput

  emit('select', selected)
  selectedEntryId.value = selected
  isProgrammaticInput.value = true
  searchQuery.value = match ? match[props.labelAttribute] : formattedInput
  entries.value = []
  activeIndex.value = -1
}

defineExpose({
  reset: resetSearch,
  setInitialDisplay: (name) => {
    isProgrammaticInput.value = true
    searchQuery.value = name
  },
  setSelectedId: (id) => {
    selectedEntryId.value = id
  },
  focus: () => {
    inputRef.value?.focus()
  },
})

const currentActiveIndex = computed(() => {
  return hoveredIndex.value !== null ? hoveredIndex.value : activeIndex.value
})

const displayedEntries = computed(() =>
  entries.value.slice(0, props.maxEntries),
)

const inputElClass = computed(() => {
  let dynamic = ''

  switch (props.borders) {
    case 'all':
      dynamic = 'border rounded'
      break

    case 'left':
      dynamic = 'border rounded-l rounded-r-none'
      break

    case 'right':
      dynamic = 'border rounded-r rounded-l-none'
      break

    case 'top/bottom':
      dynamic =
        'border border-t border-b border-l-0 border-r-0 rounded-l-none rounded-r-none'
      break

    case 'none':
      dynamic = 'border-0 focus:ring-0'
      break
  }

  const base = [
    dynamic,
    'px-3 py-2 max-w-full focus:ring focus:outline-none border-gray-700 rounded w-full',
    'dark:placeholder-gray-400 h-12',
    props.borderless ? 'border-0' : 'border',
    props.transparent ? 'bg-transparent' : 'bg-white dark:bg-slate-800',
  ]

  if (props.icon) {
    base.push('pl-10')
  }

  if (selectedEntryId.value) {
    base.push('input-selected')
  }

  return base
})

const onFocusIn = () => {
  hasFocus.value = true
  inputRef.value?.select()
}

const onFocusOut = () => {
  setTimeout(() => {
    if (isClickingEntry.value) return

    hasFocus.value = false

    if (props.allowCustomEntry) {
      selectOrCreateEntry()
    }

    if (!selectedEntryId.value && !props.allowCustomEntry) {
      searchQuery.value = ''
    }
  }, 150)
}

const showNoResultIcon = computed(() => {
  return (
    searchQuery.value.length >= 3 &&
    !isLoading.value &&
    entries.value.length === 0 &&
    !selectedEntryId.value &&
    !props.allowCustomEntry
  )
})

const showPendingIcon = computed(() => {
  return (
    searchQuery.value.length >= 3 &&
    !isLoading.value &&
    entries.value.length > 0 &&
    !selectedEntryId.value
  )
})

const effectivePlaceholder = computed(
  () => props.placeholder ?? t('common.searchPlaceholder'),
)

const handleMouseMove = (index) => {
  if (isUsingKeyboard.value) {
    isUsingKeyboard.value = false
  }

  hoveredIndex.value = index
}

watch(searchQuery, (newValue) => {
  if (isProgrammaticInput.value) {
    isProgrammaticInput.value = false
    return
  }

  if (newValue.length < 3) {
    entries.value = []
    totalCount.value = 0
  }

  if (selectedEntryId.value) {
    selectedEntryId.value = null
  }
})
</script>

<template>
  <div class="search-component relative" :class="{ dark: styleStore.darkMode }">
    <!-- Input fields -->
    <div class="relative">
      <!-- Search data input field -->
      <input
        :id="props.id"
        ref="inputRef"
        v-model="searchQuery"
        :aria-describedby="props.ariaDescribedby"
        :autocomplete="props.autocomplete"
        type="text"
        :placeholder="effectivePlaceholder"
        :class="inputElClass"
        :aria-label="t('common.search')"
        :autofocus="autofocus"
        :maxlength="props.maxlength"
        @input="onInput"
        @keydown="onKeyDown"
        @focus="onFocusIn"
        @blur="onFocusOut"
      />

      <!-- Hidden required field, if required -->
      <input
        v-if="props.required"
        tabindex="-1"
        :aria-hidden="true"
        style="opacity: 0; width: 0; height: 0; float: right"
        name="selectedEntry"
        :value="selectedEntryId || ''"
        required
      />

      <!-- Blue loading icon -->
      <div
        v-if="isLoading"
        class="absolute right-2 inset-y-0 flex items-center text-blue-500"
      >
        <svg
          class="animate-spin h-5 w-5"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />

          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v8H4z"
          />
        </svg>
      </div>

      <!-- Green ✔️ icon -->
      <div
        v-else-if="selectedEntryId"
        class="absolute right-2 inset-y-0 flex items-center"
      >
        <svg
          class="h-5 w-5 text-green-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>

      <!-- Red X icon -->
      <div
        v-else-if="showNoResultIcon"
        class="absolute right-2 inset-y-0 flex items-center"
      >
        <svg
          class="h-5 w-5 text-red-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </div>

      <!-- Blue ... icon -->
      <div
        v-else-if="showPendingIcon"
        class="absolute right-2 inset-y-0 flex items-center"
      >
        <svg
          class="h-5 w-5 text-blue-500"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <circle cx="4" cy="10" r="2" />

          <circle cx="10" cy="10" r="2" />

          <circle cx="16" cy="10" r="2" />
        </svg>
      </div>
    </div>

    <!-- Search results list -->
    <ul
      v-if="searchQuery.length >= 3 && !selectedEntryId && hasFocus"
      class="dark:bg-slate-800 mt-2 border border-color rounded-md bg-white shadow-lg p-2 absolute w-full z-50 max-h-[40vh] flex flex-col"
      role="listbox"
    >
      <!-- Scrollable area -->
      <div class="overflow-auto" style="max-height: calc(35vh - 4rem)">
        <li v-if="isLoading" class="text-sm text-gray-500 p-2 italic">
          {{ t('common.loading') }}
        </li>

        <template v-else>
          <!-- Search result entry -->
          <li
            v-for="(entry, index) in displayedEntries"
            :key="entry.id"
            :class="[
              'cursor-pointer rounded-md p-2 px-4 py-2 transition-colors duration-150',
              index === currentActiveIndex
                ? 'bg-blue-200 dark:bg-blue-500 active-entry'
                : hoveredIndex === index
                  ? 'hover:bg-blue-200 dark:hover:bg-blue-500'
                  : '',
            ]"
            role="option"
            :aria-selected="selectedEntryId === entry.id"
            @mousemove="handleMouseMove(index)"
            @click="selectEntry(entry)"
          >
            {{ entry[props.labelAttribute] }}
          </li>

          <!-- No entries found -->
          <li v-if="!entries.length" class="text-sm text-gray-500 p-2 italic">
            {{ t('common.noResults') }}
          </li>
        </template>
      </div>

      <!-- Warning: more entries were found than maxEntries allows -->
      <li
        v-if="totalCount > props.maxEntries"
        class="text-sm text-gray-500 dark:text-gray-300 p-2 rounded-md border-t border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800"
        role="presentation"
        aria-hidden="true"
        tabindex="-1"
      >
        {{
          t('components.searchField.entriesLimitHint', {
            shown: props.maxEntries,
            total: totalCount,
          })
        }}
      </li>

      <!-- Navigation help text -->
      <li
        v-if="entries.length"
        class="text-sm text-gray-500 dark:text-gray-300 p-2 rounded-md border-t border-gray-300 dark:border-gray-600 bg-white dark:bg-slate-800"
        role="presentation"
        aria-hidden="true"
        tabindex="-1"
      >
        {{ t('components.searchField.navigationHint') }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
.text-green-500 {
  color: #10b981;
}
.text-blue-500 {
  color: #3b82f6;
}
.text-red-500 {
  color: #ef4444;
}
.animate-spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
