<script setup>
import { mdiPlus, mdiSchoolOutline } from '@mdi/js'
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
import { courseSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils'
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

    const response = await backend.courses.list({
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
      t('common.loadErrorPlural', { entities: t('objectTypes.course.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

const BLOCKING_EVENTS_LIMIT = 5
const blockingEvents = ref([])
const blockingEventsTotal = ref(0)

async function openDeleteModal(object) {
  objToRemove.value = object
  blockingEvents.value = []
  blockingEventsTotal.value = 0
  backend.beginSilent()
  try {
    const result = await backend.events.list({
      page: 1,
      limit: BLOCKING_EVENTS_LIMIT,
      search_field: 'course',
      search_value: object.id,
    })
    blockingEvents.value = result?.items ?? []
    blockingEventsTotal.value =
      result?.pageDetails?.totalCount ?? blockingEvents.value.length
  } catch {
    // Fail open: without the pre-check the backend 409 still blocks the delete
  } finally {
    backend.endSilent()
  }
  modals.deleteObject.value = true
}

const blockingEventItems = computed(() => {
  const items = blockingEvents.value.map((event) => ({
    label: event.name ?? event.id,
  }))
  const more = blockingEventsTotal.value - blockingEvents.value.length
  if (more > 0) {
    items.push({
      label: t('views.courses.delete.moreEvents', { count: more }, more),
    })
  }
  return items
})

async function deleteObject(id) {
  backend.beginSilent()
  try {
    await backend.courses.delete(id)
    fetchObjects()
    toast.success(
      t('common.deleteSuccess', { entity: t('objectTypes.course.singular') }),
    )
  } catch (error) {
    const errorCode = error?.response?.data?.error_code
    if (
      errorCode === 'OBJECT_IN_USE' ||
      errorCode === 'OBJECT_DELETE_INTEGRITY_ERROR'
    ) {
      toast.error(t('views.courses.delete.blockedError'), { timeout: 8400 })
    } else {
      const detail = String(error?.response?.data?.detail || '')
      toast.error(
        `${t('common.deleteError', { entity: t('objectTypes.course.singular') })}${detail ? '\n' + detail : ''}`,
      )
    }
  } finally {
    backend.endSilent()
  }
}

const searchBarFields = courseSearchBarFields()

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions(
    'courses',
    '*',
    permissionRefs,
    [],
    ['canCreate'],
  )
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete course -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.name"
      :checkvalue="objToRemove.name"
      :blocked="blockingEventsTotal > 0"
      :info="
        blockingEventsTotal > 0 ? null : $t('views.courses.delete.cascadeInfo')
      "
      :warning="
        blockingEventsTotal > 0
          ? $t(
              'views.courses.delete.relatedWarning',
              { count: blockingEventsTotal },
              blockingEventsTotal,
            )
          : null
      "
      :related-items="blockingEventItems"
      :related-label="$t('views.courses.delete.relatedLabel')"
      :related-count="blockingEventsTotal"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiSchoolOutline"
        :title="$t('objectTypes.course.plural')"
        main
        docs-path="/docs/usage/openvle/courses/"
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
          @click="router.push({ path: `/courses/create` })"
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
          object-model="courses"
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
