<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseLevel from '@/components/BaseLevel.vue'
import FormControl from '@/components/FormControl.vue'

const { t } = useI18n()

const props = defineProps({
  currentPage: {
    type: Number,
    required: false,
    default: 0,
  },
  itemsTotal: {
    type: [Number, String],
    required: false,
    default: 0,
  },
  perPage: {
    type: Number,
    required: false,
    default: 10,
  },
  perPageSelect: {
    type: Array,
    required: false,
    default() {
      return [5, 10, 25, 50, 75, 100].map((n) => ({
        label: String(n),
        value: n,
      }))
    },
  },
  lastRefresh: {
    type: Date,
    default: null,
  },
})

const perPageSelected = ref(props.perPage)

const emit = defineEmits(['paginationChanged'])

const currentPageHuman = computed(() => props.currentPage)
const numPages = computed(() => Math.ceil(props.itemsTotal / props.perPage))

const formattedLastRefresh = computed(() => {
  if (!props.lastRefresh) return null
  return props.lastRefresh.toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
})

const pagesList = computed(() => {
  if (props.itemsTotal <= 0) return [1]

  const visibleButtons = 5
  const half = Math.floor(visibleButtons / 2)

  let startPage = Math.max(1, props.currentPage - half)
  let endPage = Math.min(startPage + visibleButtons - 1, numPages.value)

  if (endPage - startPage < visibleButtons - 1) {
    startPage = Math.max(1, endPage - visibleButtons + 1)
  }

  const list = []

  if (startPage > 1) {
    list.push(1)
    if (currentPageHuman.value > 11) {
      list.push('prev10')
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    list.push(i)
  }

  if (
    endPage < numPages.value - 1 &&
    props.currentPage + 10 <= numPages.value
  ) {
    list.push('next10')
  }

  return list
})

const onUpdate = (newValue) => {
  const parsed = Number(newValue)
  perPageSelected.value = props.perPage

  if (parsed !== props.perPage && parsed != 0) {
    perPageSelected.value = parsed
    emit('paginationChanged', props.currentPage, parsed)
  }
}
</script>

<template>
  <div class="p-3 lg:px-6 border-t border-gray-100 dark:border-slate-800">
    <BaseLevel class="mb-2">
      <BaseButtons>
        <BaseButton
          v-for="page in pagesList"
          :key="page"
          :label="
            typeof page === 'string'
              ? page === 'prev10'
                ? '-10'
                : '+10'
              : page
          "
          :color="page === currentPage ? 'lightDark' : 'whiteDark'"
          small
          rounded-full
          @click="
            typeof page === 'number'
              ? emit('paginationChanged', page, props.perPage)
              : emit(
                  'paginationChanged',
                  page === 'prev10'
                    ? Math.max(0, currentPage - 10)
                    : Math.min(numPages, currentPage + 10),
                  props.perPage,
                )
          "
        />
      </BaseButtons>

      <div class="ml-auto flex items-center gap-2">
        <label for="perPageSelect" class="text-sm">
          {{ t('components.pagination.perPage') }}
        </label>

        <FormControl
          id="perPageSelect"
          v-model="perPageSelected"
          name="perPageSelect"
          class="pr-3 min-w-20"
          :options="props.perPageSelect"
          :required="true"
          @update:model-value="onUpdate"
        />

        <small class="text-right">
          {{
            t('components.pagination.pageOfTotal', {
              current: currentPageHuman,
              total: numPages > 0 ? numPages : 1,
            })
          }}<br />

          {{
            t('components.pagination.totalEntries', {
              count: itemsTotal,
            })
          }}<br />

          <span class="text-slate-400 dark:text-slate-500">
            {{ t('components.pagination.dataAsOf') }}
            {{ formattedLastRefresh || '--:--:--' }}
          </span>
        </small>
      </div>
    </BaseLevel>
  </div>
</template>
