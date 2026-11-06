<script setup>
import { mdiCalendarOutline, mdiPlus } from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { eventSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import { useListAutoRefresh } from '@/composables/useListAutoRefresh'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { OBJECT_TYPE } from '@/stores/userSettings'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  statusEventFilter,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { eventStatusIcon } from '@/utils/icons'
import { statusColorEvent } from '@/utils/objectColors'
import { usePaginationList } from '@/utils/pagination'

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
    const response = await backend.events.list({
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
      { from: 'status', to: 'statusName', keyspace: 'eventStatus' },
    ])
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.event.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

const BLOCKING_VMS_LIMIT = 5
const blockingVms = ref([])
const blockingVmsTotal = ref(0)

async function openDeleteModal(object) {
  objToRemove.value = object
  blockingVms.value = []
  blockingVmsTotal.value = 0
  backend.beginSilent()
  try {
    const result = await backend.events.getVMs(object.id, {
      page: 1,
      limit: BLOCKING_VMS_LIMIT,
    })
    blockingVms.value = result?.items ?? []
    blockingVmsTotal.value =
      result?.pageDetails?.totalCount ?? blockingVms.value.length
  } catch {
    // Fail open: the backend 409 pre-check still blocks the delete
  } finally {
    backend.endSilent()
  }
  modals.deleteObject.value = true
}

const blockingVmRows = computed(() => {
  const items = blockingVms.value.map((vm) => ({
    label: vm.name ?? vm.id,
  }))
  const more = blockingVmsTotal.value - blockingVms.value.length
  if (more > 0) {
    items.push({
      label: t('views.events.delete.moreVms', { count: more }, more),
    })
  }
  return items
})

async function deleteObject(id) {
  backend.beginSilent()
  try {
    await backend.events.delete(id)
    fetchObjects()
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.event.singular') }),
    )
  } catch (error) {
    const errorCode = error?.response?.data?.error_code
    if (
      errorCode === 'OBJECT_IN_USE' ||
      errorCode === 'OBJECT_DELETE_INTEGRITY_ERROR'
    ) {
      toast.error(t('views.events.delete.blockedError'), { timeout: 8400 })
    } else {
      const detail = String(error?.response?.data?.detail || '')
      toast.error(
        `${t('common.deleteError', { entity: t('objectTypes.event.singular') })}${detail ? '\n' + detail : ''}`,
      )
    }
  } finally {
    backend.endSilent()
  }
}

const searchBarFields = eventSearchBarFields()

const { autoRefreshEnabled, intervalSeconds, manualReload } =
  useListAutoRefresh({
    fetch: fetchObjects,
    objectType: OBJECT_TYPE.EVENTS,
  })

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions('events', '*', permissionRefs, [], ['canCreate'])
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete event -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      :blocked="blockingVmsTotal > 0"
      :warning="
        blockingVmsTotal > 0
          ? $t(
              'views.events.delete.relatedWarning',
              { count: blockingVmsTotal },
              blockingVmsTotal,
            )
          : null
      "
      :related-items="blockingVmRows"
      :related-label="$t('views.events.delete.relatedLabel')"
      :related-count="blockingVmsTotal"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        v-model:auto-refresh-enabled="autoRefreshEnabled"
        :icon="mdiCalendarOutline"
        :title="$t('objectTypes.event.plural')"
        main
        docs-path="/docs/usage/openvle/events/"
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
          @click="router.push({ path: `/events/create` })"
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
          object-model="events"
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
              label: $t('common.description'),
              key: 'description',
            },
            {
              label: $t('common.status'),
              key: 'statusName',
              sortKey: 'status',
              icon: (value) => eventStatusIcon(value),
              color: statusColorEvent,
              filters: statusEventFilter(),
              width: '160px',
            },
          ]"
          @search-triggered="handleSearch"
          @delete-object="openDeleteModal"
          @sort-order-changed="handleSortOrderChanged"
          @pagination-changed="handlePaginationChanged"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
