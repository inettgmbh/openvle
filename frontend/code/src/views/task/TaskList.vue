<script setup>
import { mdiFileTree, mdiInformation } from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { SearchOperators } from '@/components/Tables/searchOperators'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { resolveFieldFromLookup, statusTaskFilter } from '@/utils/dataUtils'
import { taskStatusIcon } from '@/utils/icons'
import { statusColorTask } from '@/utils/objectColors'
import { usePaginationList } from '@/utils/pagination'
import { taskStatusTooltip } from '@/utils/tooltips'

const { t } = useI18n()
const toast = useToast()

const objects = ref([])

/* PAGINATION ONLY */
const dataLoading = ref(true)
const {
  currentPage,
  perPage,
  sortColumnKey,
  sortDirection,
  searchField,
  searchValue,
  handlePaginationChanged,
  handleSortOrderChanged,
  handleSearch,
  initialFetch,
} = usePaginationList({
  initialPage: 1,
  initialPerPage: 25,
  initialSortColumn: 'createdAt',
  initialSortOrder: 'desc',
  initialSearchField: null,
  initialSearchValue: null,
  fetch: fetchObjects,
  useReplace: true,
  syncQuery: true,
})
/**/

async function fetchObjects() {
  try {
    dataLoading.value = true

    const response = await backend.tasks.list({
      page: currentPage.value,
      limit: perPage.value,
      sort_by: sortColumnKey.value,
      sort_order: sortDirection.value,
      search_field: searchField.value,
      search_value: searchValue.value,
    })
    objects.value = response.items
    objects.value.count = response.pageDetails.totalCount
    await resolveFieldFromLookup(objects.value, [
      { from: 'createdById', to: 'createdBy', keyspace: 'users' },
    ])
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.task.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

const searchBarFields = [
  { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
  {
    preset: 'status',
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    options: statusTaskFilter(),
  },
  {
    preset: 'event',
    key: 'event_id',
    operators: SearchOperators.EQUALS_ONLY_ONLY,
  },
  { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
  { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
]

onMounted(() => {
  initialFetch()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiFileTree"
        title="Tasks"
        main
        docs-path="/docs/usage/openvle/system/tasks/"
        :reload="fetchObjects"
      />

      <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
        <b>{{ $t('views.tasks.list.infoNotice') }}</b>
      </NotificationBar>

      <CardBox class="mb-6" has-table>
        <BaseTable
          v-if="objects"
          :current-page="currentPage"
          :per-page="perPage"
          :items-total="objects.count"
          :data="objects"
          :sort-column-key="sortColumnKey"
          :sort-direction="sortDirection"
          :loading="dataLoading"
          object-model="tasks"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            {
              label: $t('common.name'),
              key: 'name',
              width: '400px',
            },
            {
              label: $t('common.status'),
              key: 'status',
              filters: statusTaskFilter(),
              color: statusColorTask,
              icon: (value) => taskStatusIcon(value),
              tooltip: (value) => taskStatusTooltip(value),
              formatter: ['', ''],
              width: '120px',
            },
            {
              label: $t('views.tasks.columns.triggeredBy'),
              key: 'createdBy',
              sortKey: 'createdById',
              width: '170px',
            },
          ]"
          @search-triggered="handleSearch"
          @sort-order-changed="handleSortOrderChanged"
          @pagination-changed="handlePaginationChanged"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
