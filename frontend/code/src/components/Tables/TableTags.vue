<script setup>
import { mdiEye, mdiTrashCan } from '@mdi/js'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'
import TableCheckboxCell from '@/components/Tables/TableCheckboxCell.vue'
import TablePagination from '@/components/Tables/TablePagination.vue'
import backend from '@/services'
import {
  resolveObjectTypeToFrontendURLs,
  resolveObjectTypeToGerman,
} from '@/utils/dataUtils'

const props = defineProps({
  checkable: Boolean,
  currentPage: {
    type: Number,
    required: false,
    default: 0,
  },
  data: {
    type: [Object],
    required: true,
  },
  itemsTotal: {
    type: [Number, String],
    required: false,
    default: 0,
  },
  perPage: {
    type: Number,
    required: false,
    default: 0,
  },
  sortColumnKey: {
    type: String,
    required: false,
    default: 'key',
  },
  sortDirection: {
    type: String,
    required: false,
    default: 'asc',
  },
  loading: {
    type: Boolean,
    required: false,
    default: true,
  },
  hasDelete: {
    type: Boolean,
    default: false,
  },
})
const objectModel = 'tags'
const objToRemove = ref({})
const router = useRouter()
const toast = useToast()
const { t } = useI18n()
const emit = defineEmits([
  'deleteObject',
  'paginationChanged',
  'sortOrderChanged',
])
const checkedRows = ref([])
const modals = {
  deleteObject: ref(false),
}

const handlePagination = (page, perPage) => {
  emit('paginationChanged', page, perPage, props.objectModel)
}

const handleDeleteObject = (object) => {
  objToRemove.value = object
  objToRemove.value.label = `${objToRemove?.value?.key}: ${objToRemove?.value?.value}`
  modals.deleteObject.value = true
}

const checked = (isChecked, obj) => {
  if (isChecked) {
    checkedRows.value.push(obj)
  } else {
    checkedRows.value = remove(checkedRows.value, (row) => row.id === obj.id)
  }
}

async function deleteObject(id) {
  try {
    await backend.tags.delete(id)
    emit(
      'sortOrderChanged',
      props.sortDirection,
      props.sortColumnKey,
      objectModel,
    )
    toast.success(t('components.tableTags.tagDeleted'))
  } catch (error) {
    toast.error(
      t('common.deleteError', { entity: t('objectTypes.tag.singular') }),
    )
  }
}

function sortColumn(columnKey) {
  if (props.sortColumnKey === columnKey) {
    emit(
      'sortOrderChanged',
      props.sortDirection === 'asc' ? 'desc' : 'asc',
      columnKey,
      objectModel,
    )
  } else {
    emit('sortOrderChanged', 'asc', columnKey, objectModel)
  }
  return true
}

const remove = (arr, cb) => {
  const newArr = []
  arr.forEach((item) => {
    if (!cb(item)) {
      newArr.push(item)
    }
  })
  return newArr
}

const viewObject = (objectType, objectId) => {
  router.push({
    path: `/${resolveObjectTypeToFrontendURLs[objectType]}/${objectId}`,
  })
}
</script>

<template>
  <!-- Modal: Delete tag -->
  <CardBoxDeleteModal
    v-model="modals.deleteObject.value"
    :name="objToRemove.label"
    :checkvalue="objToRemove.label"
    @form-submitted="deleteObject(objToRemove.id)"
  />

  <div v-if="checkedRows.length" class="p-3 bg-gray-100/50 dark:bg-slate-800">
    <span
      v-for="checkedRow in checkedRows"
      :key="checkedRow.id"
      class="inline-block px-2 py-1 rounded-sm mr-2 text-sm bg-gray-100 dark:bg-slate-700"
    >
      {{ checkedRow.name }}
    </span>
  </div>

  <table>
    <thead>
      <tr>
        <th v-if="checkable" />

        <th
          :class="{
            sorted: sortColumnKey === 'key',
            asc: sortDirection === 'asc',
            desc: sortDirection === 'desc',
          }"
          @click="sortColumn('key')"
        >
          {{ $t('components.tableTags.tag') }}
        </th>

        <th
          :class="{
            sorted: sortColumnKey === 'objectType',
            asc: sortDirection === 'asc',
            desc: sortDirection === 'desc',
          }"
          @click="sortColumn('objectType')"
        >
          {{ $t('components.tableTags.objectType') }} <span class="arrow" />
        </th>

        <th
          :class="{
            sorted: sortColumnKey === 'objectId',
            asc: sortDirection === 'asc',
            desc: sortDirection === 'desc',
          }"
          @click="sortColumn('objectId')"
        >
          {{ $t('components.tableTags.objectId') }} <span class="arrow" />
        </th>
      </tr>
    </thead>

    <tbody>
      <!-- Row for "no data" message -->
      <tr v-if="!itemsTotal && !props.loading">
        <td colspan="4" style="text-align: center; font-weight: bold">
          {{ $t('common.noData') }}
        </td>
      </tr>

      <!-- Row for "loading" message -->
      <tr v-if="props.loading">
        <td colspan="4" style="text-align: center; font-weight: bold">
          {{ $t('common.loading') }}
        </td>
      </tr>

      <!-- Use template to separate v-if from v-for -->
      <template v-if="!props.loading">
        <tr v-for="tag in data" :key="tag.id">
          <TableCheckboxCell v-if="checkable" @checked="checked($event, tag)" />

          <td data-:label="$t('components.tableTags.tag')">
            {{ tag.key }}: {{ tag.value }}
          </td>

          <td data-:label="$t('components.tableTags.objectType')">
            {{ resolveObjectTypeToGerman(tag.objectType) }}
          </td>

          <td data-:label="$t('components.tableTags.objectId')">
            {{ tag.objectId }}
          </td>

          <td class="before:hidden lg:w-1 whitespace-nowrap">
            <BaseButtons type="justify-start lg:justify-end" no-wrap>
              <BaseButton
                color="info"
                :icon="mdiEye"
                small
                @click="viewObject(tag.objectType, tag.objectId)"
              />

              <BaseButton
                v-if="props.hasDelete"
                color="danger"
                :icon="mdiTrashCan"
                small
                @click="handleDeleteObject(tag)"
              />
            </BaseButtons>
          </td>
        </tr>
      </template>
    </tbody>
  </table>

  <TablePagination
    :current-page="props.currentPage"
    :items-total="props.itemsTotal"
    :per-page="props.perPage"
    @pagination-changed="handlePagination"
  />
</template>
