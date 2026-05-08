<script setup>
import { mdiPlus, mdiRemoteDesktop } from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { guacamoleSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { eventCreateTypeIcon } from '@/utils/icons'
import { createTypeColorConnection } from '@/utils/objectColors'
import { usePaginationList } from '@/utils/pagination'
import { eventCreateTypeTooltip } from '@/utils/tooltips'

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
  initialPerPage: 10,
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

    const response = await backend.guacamole.list({
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
      obj.vmId = obj.vms?.[0]?.id ?? null
      obj.vmName = obj.vms?.[0]?.name ?? null
    })

    await resolveFieldFromLookup(objects.value, [
      { from: 'userId', to: 'user', keyspace: 'users' },
      { from: 'createdById', to: 'createdBy', keyspace: 'users' },
    ])
  } catch (error) {
    toast.error(
      `${t('common.loadErrorPlural', { entities: t('objectTypes.guacamole.plural') })}\n${error?.response?.data?.detail || t('common.unknownError')}`,
    )
  } finally {
    dataLoading.value = false
  }
}

async function deleteObject(id) {
  try {
    await backend.guacamole.delete(id)
    fetchObjects()
    toast.success(t('views.guacamole.list.guacamoleDeleted'))
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.guacamole.singular') }),
    )
  }
}

const searchBarFields = guacamoleSearchBarFields()

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions(
    'guacamoles',
    '*',
    permissionRefs,
    [],
    ['canCreate'],
  )
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete guacamole -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiRemoteDesktop"
        :title="$t('views.guacamole.list.connections')"
        main
        docs-path="/docs/usage/openvle/connections/"
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
          @click="router.push({ path: `/guacamoles/create` })"
        />
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
          object-model="guacamoles"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            {
              label: null,
              key: 'eventId',
              sortable: true,
              tooltip: (value) => eventCreateTypeTooltip(value),
              color: createTypeColorConnection,
              icon: (value) => eventCreateTypeIcon(value),
              formatter: ['', ''],
              width: '70px',
            },
            { key: 'name', width: '300px' },
            {
              label: $t('common.user'),
              key: 'user',
              sortKey: 'userId',
              width: '130px',
            },
            {
              label: $t('common.virtualMachine'),
              key: 'vmName',
              sortable: false,
              width: '160px',
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
