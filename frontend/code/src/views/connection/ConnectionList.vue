<script setup>
import {
  mdiMonitor,
  mdiPlus,
  mdiRemoteDesktop,
  mdiVectorArrangeAbove,
} from '@mdi/js'
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
import { connectionSearchBarFields } from '@/components/Tables/searchBarFieldConfigs'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import {
  checkObjectPermissions,
  protocolConnectionFilter,
  resolveFieldFromLookup,
  usePermissionRefs,
} from '@/utils/dataUtils'
import { connectionProtocolFormatterIcon } from '@/utils/icons'
import { protocolColorConnection } from '@/utils/objectColors.js'
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
  initialPerPage: 10,
  initialSortColumn: 'createdAt',
  initialSortOrder: 'desc',
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

    const response = await backend.connections.list({
      page: currentPage.value,
      limit: perPage.value,
      sort_by: sortColumnKey.value,
      sort_order: sortDirection.value,
      search_field: searchField.value,
      search_value: searchValue.value,
    })
    objects.value = response.items
    objects.value.count = response.pageDetails.totalCount
    const templateObjects = objects.value
      .filter((obj) => obj.objectType === 'Template')
      .map((obj) => ({
        ...obj,
        objectType: 'VM-Vorlage',
      }))
    const vmObjects = objects.value
      .filter((obj) => obj.objectType === 'VirtualMachine')
      .map((obj) => ({
        ...obj,
        objectType: 'VM',
      }))
    if (templateObjects.length > 0) {
      await resolveFieldFromLookup(templateObjects, [
        { from: 'objectId', to: 'objectName', keyspace: 'templates' },
      ])
    }
    if (vmObjects.length > 0) {
      await resolveFieldFromLookup(vmObjects, [
        { from: 'objectId', to: 'objectName', keyspace: 'vms' },
      ])
    }
    objects.value = [...templateObjects, ...vmObjects]
    objects.value.count = response.pageDetails.totalCount
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.guacamole.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

async function deleteObject(id) {
  try {
    await backend.connections.delete(id)
    fetchObjects()
    toast.success(
      t('common.deleteSuccess', {
        entity: t('objectTypes.guacamoleConnectionProfile.singular'),
      }),
    )
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.guacamole.singular') }),
    )
  }
}

const searchBarFields = connectionSearchBarFields()

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions(
    'guacamole_connection_profiles',
    '*',
    permissionRefs,
    [],
    ['canCreate'],
  )
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: Delete connection profile -->
    <CardBoxDeleteModal
      v-model="modals.deleteObject.value"
      :name="objToRemove.id"
      checkvalue="Bestätigung"
      @form-submitted="deleteObject(objToRemove.id)"
    />

    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiRemoteDesktop"
        :title="$t('views.connections.list.connectionTemplates')"
        main
        docs-path="/docs/usage/openvle/connections/"
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
          @click="router.push({ path: `/connections/create` })"
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
          object-model="connections"
          :buttons="['view']"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            {
              label: $t('common.object'),
              key: 'objectName',
              sortKey: 'objectId',
              width: '220px',
            },
            {
              label: $t('common.type'),
              key: 'objectType',
              width: '120px',
              filters: [
                {
                  value: 'VirtualMachine',
                  label: 'VM',
                  icon: mdiMonitor,
                },
                {
                  value: 'Template',
                  label: 'VM-Vorlage',
                  icon: mdiVectorArrangeAbove,
                },
              ],
            },
            {
              key: 'username',
              width: '180px',
            },
            {
              label: $t('common.protocol'),
              key: 'protocol',
              color: protocolColorConnection,
              icon: (value) => connectionProtocolFormatterIcon(value),
              formatter: (value) => String(value).toUpperCase(),
              filters: protocolConnectionFilter(),
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
