<script setup>
import { mdiCloudLockOutline, mdiInformation, mdiPlus } from '@mdi/js'
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
import {
  checkObjectPermissions,
  statusUserFilter,
  usePermissionRefs,
  userStatusLabel,
} from '@/utils/dataUtils'
import { scimEnabledIcon, userStatusIcon } from '@/utils/icons'
import { statusColorScimEnabled, statusColorUser } from '@/utils/objectColors'
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

    const response = await backend.scimProviders.list({
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
      t('common.deleteError', {
        entity: t('objectTypes.scimProvider.singular'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function deleteObject(id) {
  try {
    await backend.scimProviders.delete(id)
    fetchObjects()
    toast.success(t('views.scimProviders.list.scimProviderDeleted'))
  } catch (error) {
    toast.error(
      t('common.deleteError', {
        entity: t('objectTypes.scimProvider.singular'),
      }),
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
    'scim_providers',
    '*',
    permissionRefs,
    [],
    ['canCreate'],
  )
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete provider -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiCloudLockOutline"
        :title="$t('views.scimProviders.list.scimProviders')"
        docs-path="/docs/usage/openvle/access-control/scim-providers/"
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
          @click="router.push({ path: `/scim/providers/create` })"
        />
      </SectionTitleLineWithButton>

      <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
        SCIM Provider ermöglichen die automatische Benutzerprovisionierung aus
        externen Identitätssystemen (z.B. Authentik, Okta) in dieses System.
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
          object-model="scim/providers"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            { key: 'name', width: '300px' },
            { key: 'description' },
            {
              label: $t('common.userStatus'),
              key: 'default_user_status',
              color: statusColorUser,
              icon: (value) => userStatusIcon(value),
              formatter: (value) => userStatusLabel(value),
              filters: statusUserFilter(),
              width: '200px',
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
