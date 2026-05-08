<script setup>
import { mdiImport, mdiPlus, mdiVectorArrangeAbove } from '@mdi/js'
import { onMounted, ref } from 'vue'
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

async function deleteObject(id) {
  try {
    await backend.templates.delete(id)
    fetchObjects()
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.template.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.template.singular') }),
    )
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
          @delete-object="handleDeleteObject"
          @sort-order-changed="handleSortOrderChanged"
          @pagination-changed="handlePaginationChanged"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
