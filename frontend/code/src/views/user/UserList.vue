<script setup>
import { mdiAccount, mdiImport, mdiPlus } from '@mdi/js'
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
import { userSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  usePermissionRefs,
  userStatusLabel,
} from '@/utils/dataUtils'
import { userStatusIcon } from '@/utils/icons'
import { statusColorUser } from '@/utils/objectColors.js'
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

    const response = await backend.users.list({
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
      t('common.loadErrorPlural', { entities: t('objectTypes.user.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function deleteObject(id) {
  try {
    await backend.users.delete(id)
    fetchObjects()
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.user.singular') }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.user.singular') }),
    )
  }
}

const searchBarFields = userSearchBarFields()

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions('users', '*', permissionRefs, [], ['canCreate'])
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete user -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiAccount"
        :title="$t('objectTypes.user.plural')"
        main
        docs-path="/docs/usage/openvle/access-control/users/"
        :reload="fetchObjects"
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
            @click="router.push({ path: `/users/import` })"
          />

          <BaseButton
            target="_blank"
            :icon="mdiPlus"
            :label="$t('common.add')"
            color="contrast"
            rounded-full
            small
            @click="router.push({ path: `/users/create` })"
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
          object-model="users"
          :buttons="['view']"
          :symbol="true"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            { label: 'symbol', key: 'id', symbol: true, width: '50px' },
            { label: $t('common.name'), key: 'name' },
            {
              label: $t('views.users.form.username'),
              key: 'username',
              width: '190px',
            },
            {
              label: $t('views.users.form.emailShort'),
              key: 'email',
              width: '173px',
            },
            {
              label: $t('common.status'),
              key: 'status',
              color: statusColorUser,
              icon: (value) => userStatusIcon(value),
              formatter: (value) => userStatusLabel(value),
              width: '180px',
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
