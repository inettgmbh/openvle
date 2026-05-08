<script setup>
import { mdiIp, mdiKeyOutline, mdiTextBox, mdiWeb } from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { SearchOperators } from '@/components/Tables/searchOperators'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  methodHTTPFilters,
  resolveFieldFromLookup,
  responseCodeHTTPFilters,
} from '@/utils/dataUtils'
import { methodHTTPIcon, responseCodeHTTPIcon } from '@/utils/icons'
import {
  responseCodeColorActivity,
  responseMethodColorActivity,
} from '@/utils/objectColors.js'
import { usePaginationList } from '@/utils/pagination'

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
  initialSortColumn: 'timestamp',
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

    const response = await backend.activities.list({
      page: currentPage.value,
      limit: perPage.value,
      sort_by: sortColumnKey.value,
      sort_order: sortDirection.value,
      search_field: searchField.value,
      search_value: searchValue.value,
    })
    objects.value = response.items
    objects.value.count = response.pageDetails.totalCount

    objects.value.forEach((obj) => {
      obj.userIds = obj.requestUser?.id
    })

    await resolveFieldFromLookup(objects.value, [
      { from: 'userIds', to: 'requestUsername', keyspace: 'users' },
    ])

    objects.value.forEach((obj) => {
      if (!obj.requestUsername || obj.requestUsername.trim() === '') {
        obj.requestUsername = obj.requestUser?.username
      }
    })
  } catch (error) {
    toast.error(
      `${t('common.loadErrorPlural', { entities: t('objectTypes.activity.plural') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    dataLoading.value = false
  }
}

const searchBarFields = [
  {
    key: 'requestClientIP',
    label: t('views.activities.list.ipAddress'),
    icon: mdiIp,
    operators: SearchOperators.CONTAINS_ONLY,
  },
  {
    key: 'requestUrl',
    label: t('common.url'),
    icon: mdiWeb,
    operators: SearchOperators.CONTAINS_ONLY,
  },
  {
    key: 'requestMethod',
    label: t('views.activities.list.method'),
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    options: methodHTTPFilters(),
  },
  {
    key: 'responseCode',
    label: t('common.response'),
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    options: responseCodeHTTPFilters(),
  },
  {
    key: 'requestPermission',
    label: t('views.activities.detail.requestPermission'),
    icon: mdiKeyOutline,
    operators: SearchOperators.CONTAINS_ONLY,
  },
]

onMounted(() => {
  initialFetch()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiTextBox"
        :title="$t('objectTypes.activity.plural')"
        main
        docs-path="/docs/usage/openvle/system/activities/"
        :reload="fetchObjects"
      >
      </SectionTitleLineWithButton>

      <CardBox class="mb-6" has-table>
        <BaseTable
          v-if="objects"
          :current-page="currentPage"
          :per-page="perPage"
          :items-total="objects.count"
          :data="objects"
          :sort-column-key="sortColumnKey"
          created-column-key="timestamp"
          :sort-direction="sortDirection"
          :loading="dataLoading"
          object-model="activities"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            {
              label: $t('views.activities.list.ipAddress'),
              key: 'requestClientIP',
              width: '150px',
            },
            {
              label: $t('objectTypes.user.singular'),
              key: 'requestUsername',
              sortKey: 'requestUser',
              width: '150px',
            },
            {
              label: $t('views.activities.list.method'),
              key: 'requestMethod',
              color: responseMethodColorActivity,
              icon: (value) => methodHTTPIcon(value),
              filters: methodHTTPFilters(),
              width: '130px',
            },
            {
              label: $t('common.url'),
              key: 'requestUrl',
              width: '200px',
            },
            {
              label: $t('common.response'),
              key: 'responseCode',
              color: responseCodeColorActivity,
              icon: (value) => responseCodeHTTPIcon(value),
              filters: responseCodeHTTPFilters(),
              width: '120px',
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
