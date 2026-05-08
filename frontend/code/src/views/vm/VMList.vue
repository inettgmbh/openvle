<script setup>
import { mdiMonitor, mdiPlus } from '@mdi/js'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { vmSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import { useListAutoRefresh } from '@/composables/useListAutoRefresh'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { OBJECT_TYPE } from '@/stores/userSettings'
import {
  checkObjectPermissions,
  statusVMFilter,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { eventCreateTypeIcon, vmStatusIcon } from '@/utils/icons'
import {
  createTypeColorConnection,
  statusColorVM,
} from '@/utils/objectColors.js'
import { usePaginationList } from '@/utils/pagination'
import { eventCreateTypeTooltip } from '@/utils/tooltips'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()
const router = useRouter()
const toast = useToast()

const objects = ref([])

/* PAGINATION ONLY */
const dataLoading = ref(true)
const objToRemove = ref({})
const modals = {
  deleteObject: ref(false),
  deleteVmsForReal: ref(false),
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
    const response = await backend.vms.list({
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
        entities: t('objectTypes.virtualMachine.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

const searchBarFields = vmSearchBarFields()

const { autoRefreshEnabled, intervalSeconds, manualReload } =
  useListAutoRefresh({
    fetch: fetchObjects,
    objectType: OBJECT_TYPE.VMS,
  })

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions('vms', '*', permissionRefs, [], ['canCreate'])
})

async function deleteObject(id) {
  try {
    await backend.vms.delete(id)
    fetchObjects()
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', {
        entity: t('objectTypes.virtualMachine.singular'),
      }),
    )
  }
}
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete vm -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      @form-submitted="modals.deleteVmsForReal.value = true"
    />

    <CardBoxModal
      v-model="modals.deleteVmsForReal.value"
      :title="$t('views.vms.list.confirmAction')"
      button="danger"
      has-cancel
      :button-label="$t('common.delete')"
      @form-submitted="deleteObject(objToRemove.id)"
    >
      <p>
        <b>{{ $t('views.vms.list.cannotBeUndone') }}</b>
      </p>

      <p>
        <b>{{ $t('views.vms.list.areYouSure') }}</b>
      </p>
    </CardBoxModal>

    <SectionMain>
      <SectionTitleLineWithButton
        v-model:auto-refresh-enabled="autoRefreshEnabled"
        :icon="mdiMonitor"
        :title="$t('views.templates.detail.virtualMachines')"
        main
        docs-path="/docs/usage/openvle/vms/"
        :reload="manualReload"
        :auto-refresh-interval-seconds="intervalSeconds"
      >
        <BaseButton
          v-if="permissionRefs.canCreate"
          target="_blank"
          :icon="mdiPlus"
          :label="$t('common.add')"
          color="contrast"
          rounded-full
          small
          @click="router.push({ path: `/vms/create` })"
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
          object-model="vms"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            {
              label: null,
              key: 'event',
              sortable: true,
              tooltip: (value) => eventCreateTypeTooltip(value),
              color: createTypeColorConnection,
              icon: (value) => eventCreateTypeIcon(value),
              formatter: ['', ''],
              width: '70px',
            },
            {
              label: $t('common.name'),
              key: 'name',
              width: '275px',
            },
            {
              label: $t('common.description'),
              key: 'description',
              markdown: true,
            },
            {
              label: $t('common.status'),
              key: 'status',
              color: statusColorVM,
              icon: (value) => vmStatusIcon(value),
              filters: statusVMFilter(),
              width: '140px',
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
