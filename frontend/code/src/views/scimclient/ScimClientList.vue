<script setup>
import { mdiCloudSyncOutline, mdiInformation, mdiPlus } from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { SearchOperators } from '@/components/Tables/searchOperators'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils'
import { scimEnabledIcon } from '@/utils/icons'
import { statusColorScimEnabled } from '@/utils/objectColors'
import { usePaginationList } from '@/utils/pagination'

const permissionRefs = usePermissionRefs()
const router = useRouter()
const toast = useToast()
const { t } = useI18n()

const objects = ref([])

/* PAGINATION ONLY */
const dataLoading = ref(true)
const objToRemove = ref({})
const modals = {
  deleteObject: ref(false),
}
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

    const response = await backend.scimClients.list({
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
        entities: t('objectTypes.scimClient.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function deleteObject(id) {
  try {
    await backend.scimClients.delete(id)
    fetchObjects()
    toast.success(t('views.scimClients.list.scimClientDeleted'))
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.scimClient.singular') }),
    )
  }
}

const searchBarFields = [
  { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'description', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
  { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
]

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions(
    'scim_clients',
    '*',
    permissionRefs,
    [],
    ['canCreate'],
  )
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete client -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiCloudSyncOutline"
        :title="$t('views.scimClients.list.scimClients')"
        docs-path="/docs/usage/openvle/access-control/scim-clients/"
        main
        :reload="fetchObjects"
      >
        <BaseButton
          v-if="permissionRefs.canCreate"
          target="_blank"
          :icon="mdiPlus"
          :label="$t('common.add')"
          color="contrast"
          rounded-full
          small
          @click="router.push({ path: `/scim/clients/create` })"
        />
      </SectionTitleLineWithButton>

      <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
        SCIM Clients synchronisieren lokale Benutzer und Rollen automatisch zu
        externen Zielsystemen.
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
          object-model="scim/clients"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            { key: 'name', width: '250px' },
            { key: 'description' },
            {
              label: 'Endpoint URL',
              key: 'endpoint_url',
              width: '300px',
            },
            {
              label: $t('common.status'),
              key: 'enabled',
              color: statusColorScimEnabled,
              icon: (value) => scimEnabledIcon(value),
              formatter: [$t('common.active'), $t('common.inactive')],
              width: '120px',
            },
          ]"
          @search-triggered="handleSearch"
          @delete-object="handleDeleteObject"
          @sort-order-changed="handleSortOrderChanged"
          @pagination-changed="handlePaginationChanged"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
