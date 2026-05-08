<script setup>
import { mdiListBoxOutline } from '@mdi/js'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import CardBox from '@/components/CardBox.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TableChangelogs from '@/components/Tables/TableChangelogs.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { usePaginationList } from '@/utils/pagination'

const toast = useToast()
const { t } = useI18n()

const objects = ref([])

/* PAGINATION ONLY */
const {
  currentPage,
  perPage,
  sortColumnKey,
  sortDirection,
  handlePaginationChanged,
  handleSortOrderChanged,
} = usePaginationList({
  initialPage: 1,
  initialPerPage: 10,
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
    const response = await backend.changelog.list({
      page: currentPage.value,
      limit: perPage.value,
      sort_by: sortColumnKey.value,
      sort_order: sortDirection.value,
    })
    objects.value = response.items
    objects.value.count = response.pageDetails.totalCount
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.changelog.plural'),
      }),
    )
  }
}
fetchObjects()
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiListBoxOutline"
        :title="$t('views.changelogs.list.changelogs')"
        main
        :reload="fetchObjects"
      >
      </SectionTitleLineWithButton>

      <CardBox class="mb-6" has-table>
        <TableChangelogs
          v-if="objects"
          :all="true"
          :current-page="currentPage"
          :per-page="perPage"
          :items-total="objects.count"
          :data="objects"
          :sort-column-key="sortColumnKey"
          :sort-direction="sortDirection"
          @sort-order-changed="handleSortOrderChanged"
          @pagination-changed="handlePaginationChanged"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
