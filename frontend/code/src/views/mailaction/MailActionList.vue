<script setup>
import { mdiEmailSync } from '@mdi/js'
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
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils'
import { usePaginationList } from '@/utils/pagination'

const permissionRefs = usePermissionRefs()
const toast = useToast()
const { t } = useI18n()

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
  handleDeleteObject,
  initialFetch,
} = usePaginationList({
  initialPage: 1,
  initialPerPage: 25,
  initialSortColumn: 'name',
  initialSortOrder: 'asc',
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

    const response = await backend.mailActions.list({
      page: currentPage.value,
      limit: perPage.value,
      sort_by: sortColumnKey.value,
      sort_order: sortDirection.value,
      search_field: searchField.value,
      search_value: searchValue.value,
    })
    objects.value = response.items
    objects.value.count = response.pageDetails.totalCount
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.mailAction.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

const searchBarFields = [
  { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'slug', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'description', operators: SearchOperators.CONTAINS_ONLY },
]

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions('mail_templates', '*', permissionRefs, [], [])
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiEmailSync"
        :title="$t('objectTypes.mailAction.plural')"
        main
        docs-path="/docs/usage/openvle/mails/"
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
          :sort-direction="sortDirection"
          :loading="dataLoading"
          object-model="mail-actions"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[{ key: 'name', width: '420px' }, { key: 'description' }]"
          @search-triggered="handleSearch"
          @delete-object="handleDeleteObject"
          @sort-order-changed="handleSortOrderChanged"
          @pagination-changed="handlePaginationChanged"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
