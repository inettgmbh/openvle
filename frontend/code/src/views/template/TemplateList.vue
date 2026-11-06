<script setup>
import { mdiImport, mdiPlus, mdiVectorArrangeAbove } from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { templateSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import { useListAutoRefresh } from '@/composables/useListAutoRefresh'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { OBJECT_TYPE } from '@/stores/userSettings'
import {
  checkObjectPermissions,
  statusTemplateFilter,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { templateStatusIcon } from '@/utils/icons'
import { statusColorTemplates } from '@/utils/objectColors'
import { usePaginationList } from '@/utils/pagination'
import { templateStatusTooltip } from '@/utils/tooltips'

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

    const response = await backend.templates.list({
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
        entities: t('objectTypes.template.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

const BLOCKING_ITEMS_LIMIT = 5
const blockingItems = ref([])
const blockingItemsTotal = ref(0)

async function openDeleteModal(object) {
  objToRemove.value = object
  blockingItems.value = []
  blockingItemsTotal.value = 0
  backend.beginSilent()
  try {
    const [vms, courses] = await Promise.all([
      backend.templates.getVMs(object.id, {
        page: 1,
        limit: BLOCKING_ITEMS_LIMIT,
      }),
      backend.templates.getCourses(object.id, {
        page: 1,
        limit: BLOCKING_ITEMS_LIMIT,
      }),
    ])
    const vmItems = (vms?.items ?? []).map((vm) => ({
      label: vm.name ?? vm.id,
      sublabel: t('objectTypes.virtualMachine.singular'),
    }))
    const courseItems = (courses?.items ?? []).map((course) => ({
      label: course.name ?? course.id,
      sublabel: t('objectTypes.course.singular'),
    }))
    blockingItems.value = [...vmItems, ...courseItems].slice(
      0,
      BLOCKING_ITEMS_LIMIT,
    )
    blockingItemsTotal.value =
      (vms?.pageDetails?.totalCount ?? vmItems.length) +
      (courses?.pageDetails?.totalCount ?? courseItems.length)
  } catch {
    // Fail open: the backend 409 pre-check still blocks the delete
  } finally {
    backend.endSilent()
  }
  modals.deleteObject.value = true
}

const blockingItemRows = computed(() => {
  const items = blockingItems.value.slice()
  const more = blockingItemsTotal.value - items.length
  if (more > 0) {
    items.push({
      label: t('views.templates.delete.moreItems', { count: more }, more),
    })
  }
  return items
})

async function deleteObject(id) {
  backend.beginSilent()
  try {
    await backend.templates.delete(id)
    fetchObjects()
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.template.singular') }),
    )
  } catch (error) {
    const errorCode = error?.response?.data?.error_code
    if (
      errorCode === 'OBJECT_IN_USE' ||
      errorCode === 'OBJECT_DELETE_INTEGRITY_ERROR'
    ) {
      toast.error(t('views.templates.delete.blockedError'), { timeout: 8400 })
    } else {
      const detail = String(error?.response?.data?.detail || '')
      toast.error(
        `${t('common.deleteError', { entity: t('objectTypes.template.singular') })}${detail ? '\n' + detail : ''}`,
      )
    }
  } finally {
    backend.endSilent()
  }
}

const searchBarFields = templateSearchBarFields()

const { autoRefreshEnabled, intervalSeconds, manualReload } =
  useListAutoRefresh({
    fetch: fetchObjects,
    objectType: OBJECT_TYPE.TEMPLATES,
  })

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions(
    'templates',
    '*',
    permissionRefs,
    [],
    ['canCreate'],
  )
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete template -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      :blocked="blockingItemsTotal > 0"
      :warning="
        blockingItemsTotal > 0
          ? $t(
              'views.templates.delete.relatedWarning',
              { count: blockingItemsTotal },
              blockingItemsTotal,
            )
          : null
      "
      :related-items="blockingItemRows"
      :related-label="$t('views.templates.delete.relatedLabel')"
      :related-count="blockingItemsTotal"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        v-model:auto-refresh-enabled="autoRefreshEnabled"
        :icon="mdiVectorArrangeAbove"
        :title="$t('objectTypes.template.plural')"
        main
        docs-path="/docs/usage/openvle/vms/templates/"
        :reload="manualReload"
        :auto-refresh-interval-seconds="intervalSeconds"
      >
        <BaseButtons
          v-if="permissionRefs.canCreate"
          type="justify-start lg:justify-end"
        >
          <BaseButton
            target="_blank"
            :icon="mdiImport"
            :label="$t('common.import')"
            color="contrast"
            rounded-full
            small
            @click="router.push({ path: `/templates/import` })"
          />

          <BaseButton
            target="_blank"
            :icon="mdiPlus"
            :label="$t('common.add')"
            color="contrast"
            rounded-full
            small
            @click="router.push({ path: `/templates/create` })"
          />
        </BaseButtons>
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
          object-model="templates"
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
              markdown: true,
            },
            {
              label: $t('common.status'),
              key: 'status',
              color: statusColorTemplates,
              icon: (value) => templateStatusIcon(value),
              formatter: ['', ''],
              filters: statusTemplateFilter(),
              tooltip: (value) => templateStatusTooltip(value),
              width: '140px',
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
