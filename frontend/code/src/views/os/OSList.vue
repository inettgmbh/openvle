<script setup>
import { mdiApplicationBrackets, mdiPlus } from '@mdi/js'
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
import { osSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
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

    const response = await backend.os.list({
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
      { from: 'vendor', to: 'vendorName', keyspace: 'vendors' },
    ])
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.os.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function deleteObject(id) {
  try {
    await backend.os.delete(id)
    fetchObjects()
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.os.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.os.singular') }),
    )
  }
}

const searchBarFields = osSearchBarFields()

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions('os', '*', permissionRefs, [], ['canCreate'])
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete os -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiApplicationBrackets"
        :title="$t('objectTypes.os.plural')"
        main
        docs-path="/docs/usage/openvle/infrastructure/os/"
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
          @click="router.push({ path: `/os/create` })"
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
          object-model="os"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            {
              label: $t('common.name'),
              key: 'name',
              width: '300px',
            },
            {
              label: $t('objectTypes.vendor.singular'),
              key: 'vendorName',
              sortKey: 'vendor',
              width: '200px',
            },
            {
              label: $t('common.description'),
              key: 'description',
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
