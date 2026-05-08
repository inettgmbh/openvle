<script setup>
import { mdiMailboxOutline } from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { mailSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { emailStatusFormatter } from '@/utils/dataUtils'
import { emailStatusIcon, mailCreateTypeIcon } from '@/utils/icons'
import { createTypeColorMail, statusColorMail } from '@/utils/objectColors'
import { usePaginationList } from '@/utils/pagination'
import { mailCreateTypeTooltip } from '@/utils/tooltips'

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

    const response = await backend.mails.list({
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
      t('common.loadErrorPlural', { entities: t('objectTypes.mail.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

const searchBarFields = mailSearchBarFields()

onMounted(async () => {
  initialFetch()
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiMailboxOutline"
        :title="$t('objectTypes.mail.plural')"
        main
        docs-path="/docs/usage/openvle/mails/sent/"
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
          object-model="mails"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            {
              label: null,
              key: 'event',
              sortable: true,
              tooltip: (value) => mailCreateTypeTooltip(value),
              color: createTypeColorMail,
              icon: (value) => mailCreateTypeIcon(value),
              formatter: ['', ''],
              width: '70px',
            },
            {
              label: $t('views.mails.columns.subject'),
              key: 'subject',
            },
            {
              label: $t('views.mails.columns.recipient'),
              key: 'toMail',
              width: '320px',
            },
            {
              label: $t('common.status'),
              key: 'sendStatus',
              color: statusColorMail,
              icon: (value) => emailStatusIcon(value),
              formatter: (value) => emailStatusFormatter(value),
              width: '170px',
              filters: [
                {
                  value: 'sent',
                  label: $t('status.sent'),
                  icon: emailStatusIcon('sent'),
                },
                {
                  value: 'error',
                  label: $t('views.mails.filters.failed'),
                  icon: emailStatusIcon('error'),
                },
                {
                  value: 'queued',
                  label: $t('views.mails.filters.queued'),
                  icon: emailStatusIcon('queued'),
                },
              ],
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
