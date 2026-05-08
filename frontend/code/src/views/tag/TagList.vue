<script setup>
import { mdiChartBoxOutline, mdiLabel, mdiMagnify, mdiTag } from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentBody from '@/components/CardBoxComponentBody.vue'
import CardBoxComponentFooter from '@/components/CardBoxComponentFooter.vue'
import CardBoxComponentHeader from '@/components/CardBoxComponentHeader.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import TableTags from '@/components/Tables/TableTags.vue'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils'
import { usePaginationList } from '@/utils/pagination'

const { t } = useI18n()
const objects = ref([])
const permissionRefs = usePermissionRefs()
const permissionsLoaded = ref(false)
const route = useRoute()
const router = useRouter()
const toast = useToast()

/* PAGINATION ONLY */
const dataLoading = ref(true)
const searchKey = ref('')
const {
  currentPage,
  perPage,
  sortColumnKey,
  sortDirection,
  searchValue,
  handlePaginationChanged,
  handleSortOrderChanged,
} = usePaginationList({
  initialPage: 1,
  initialPerPage: 25,
  initialSortColumn: 'key',
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

    let response = []
    if (route.params.value) {
      response = await backend.tags.listByKeyValue(
        route.params.key,
        route.params.value,
        {
          page: currentPage.value,
          limit: perPage.value,
          sort_by: sortColumnKey.value,
          sort_order: sortDirection.value,
        },
      )
    } else if (route.params.key) {
      response = await backend.tags.listByKey(route.params.key, {
        page: currentPage.value,
        limit: perPage.value,
        sort_by: sortColumnKey.value,
        sort_order: sortDirection.value,
      })
    } else {
      response = await backend.tags.list({
        page: currentPage.value,
        limit: perPage.value,
        sort_by: sortColumnKey.value,
        sort_order: sortDirection.value,
      })
    }
    objects.value = response.items
    objects.value.count = response.pageDetails.totalCount
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', { entities: t('objectTypes.tag.plural') }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function search() {
  route.params.key = searchKey.value
  route.params.value = searchValue.value
  fetchObjects()
  router.push({ path: `/tags/${searchKey.value}/${searchValue.value}` })
}

async function reset() {
  route.params.key = ''
  route.params.value = ''
  fetchObjects()
  router.push({ path: `/tags` })
}

const siteTitle = computed(() => {
  if (route.params.value) {
    return t('views.tags.list.titleKeyValue', {
      key: route.params.key,
      value: route.params.value,
    })
  } else if (route.params.key) {
    return t('views.tags.list.titleKey', { key: route.params.key })
  }
  return 'Tags'
})

onMounted(async () => {
  fetchObjects()
  searchKey.value = route.params.key ? route.params.key : ''
  searchValue.value = route.params.value ? route.params.value : ''

  await checkObjectPermissions('tags', route.params.id, permissionRefs, [])

  permissionsLoaded.value = true
})
</script>

<template>
  <LayoutAuthenticated>
    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiTag"
        :title="siteTitle"
        main
        docs-path="/docs/usage/openvle/tags/"
        :reload="fetchObjects"
      />

      <CardBox is-form class="mb-6" @submit.prevent="search">
        <CardBoxComponentHeader
          :title="$t('common.search')"
        ></CardBoxComponentHeader>

        <CardBoxComponentBody>
          <FormField>
            <FormField
              :label="$t('views.tags.list.nameLabel')"
              :help="$t('views.tags.list.nameHelp')"
            >
              <FormControl v-model="searchKey" :icon="mdiLabel" required />
            </FormField>

            <FormField
              :label="$t('common.value')"
              :help="$t('views.tags.list.valueHelp')"
            >
              <FormControl v-model="searchValue" :icon="mdiChartBoxOutline" />
            </FormField>
          </FormField>

          <div class="text-xs text-gray-500 dark:text-slate-400">
            <b>{{ $t('views.tags.list.noteLabel') }} </b
            >{{ $t('views.tags.list.noteText') }}
          </div>
        </CardBoxComponentBody>

        <CardBoxComponentFooter>
          <BaseButtons>
            <BaseButton
              :label="$t('common.search')"
              type="submit"
              :icon="mdiMagnify"
              color="info"
            />

            <BaseButton
              type="reset"
              color="info"
              :label="$t('common.reset')"
              outline
              @click="reset()"
            />
          </BaseButtons>
        </CardBoxComponentFooter>
      </CardBox>

      <CardBox class="mb-6" has-table>
        <TableTags
          v-if="objects"
          :current-page="currentPage"
          :per-page="perPage"
          :items-total="objects.count"
          :data="objects"
          :sort-column-key="sortColumnKey"
          :sort-direction="sortDirection"
          :loading="dataLoading"
          :has-delete="permissionRefs.canDelete"
          @sort-order-changed="handleSortOrderChanged"
          @pagination-changed="handlePaginationChanged"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>
