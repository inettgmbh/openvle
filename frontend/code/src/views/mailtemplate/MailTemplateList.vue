<script setup>
import { mdiMailboxOutline, mdiPlus } from '@mdi/js'
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
import { SearchOperators } from '@/components/Tables/searchOperators'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useLookupStore } from '@/stores/lookup'
import {
  checkObjectPermissions,
  keyToFlag,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { statusColorMailTemplate } from '@/utils/objectColors'
import { usePaginationList } from '@/utils/pagination'

const { t } = useI18n()
const lookupStore = useLookupStore()
const permissionRefs = usePermissionRefs()
const router = useRouter()
const toast = useToast()

const objects = ref([])

lookupStore.fetchAll('languages')

const languageNameMap = computed(() => {
  const map = {}
  for (const [id, val] of Object.entries(lookupStore.languages)) {
    if (typeof val === 'object') map[id] = val.name
  }
  return map
})

const languageFlagMap = computed(() => {
  const map = {}
  for (const [id, val] of Object.entries(lookupStore.languages)) {
    if (typeof val === 'object') map[id] = keyToFlag(val.key)
  }
  return map
})

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

    const response = await backend.mailTemplates.list({
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
        entities: t('objectTypes.mailTemplate.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function deleteObject(id) {
  try {
    await backend.mailTemplates.delete(id)
    fetchObjects()
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.mailTemplate.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', {
        entity: t('objectTypes.mailTemplate.singular'),
      }),
    )
  }
}

const searchBarFields = [
  { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'subject', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'replyTo', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'description', operators: SearchOperators.CONTAINS_ONLY },
  { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
  { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
  { preset: 'language', operators: SearchOperators.EQUALS_ONLY_ONLY },
  { preset: 'mailAction', operators: SearchOperators.EQUALS_ONLY_ONLY },
]

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions(
    'mail_templates',
    '*',
    permissionRefs,
    [],
    ['canCreate'],
  )
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete mail template -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiMailboxOutline"
        :title="$t('objectTypes.mailTemplate.plural')"
        main
        docs-path="/docs/usage/openvle/mails/templates/"
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
          @click="router.push({ path: `/mail-templates/create` })"
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
          object-model="mail-templates"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            {
              label: $t('common.name'),
              key: 'name',
              width: '380px',
            },
            {
              label: $t('common.description'),
              key: 'description',
              width: '200px',
            },
            {
              label: $t('views.mailTemplates.form.language'),
              key: 'language',
              color: () => 'info',
              formatter: (value) => languageFlagMap[value] || '',
              tooltip: (value) => languageNameMap[value] || '',
              width: '100px',
            },
            {
              label: $t('views.mailTemplates.list.inUse'),
              key: 'mail_action',
              color: statusColorMailTemplate,
              formatter: ['✓', '✕'],
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
