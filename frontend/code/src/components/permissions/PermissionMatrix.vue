<script setup>
import {
  mdiCancel,
  mdiCheckboxBlankOutline,
  mdiCheckboxMultipleMarked,
  mdiChevronDown,
  mdiChevronUp,
  mdiContentSaveAll,
  mdiKey,
  mdiPencil,
  mdiPlus,
} from '@mdi/js'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import { useObjectLabelCache } from '@/components/permissions/composables/useObjectLabelCache'
import { usePermissionBulkActions } from '@/components/permissions/composables/usePermissionBulkActions'
import { usePermissionDraft } from '@/components/permissions/composables/usePermissionDraft'
import { usePermissionRows } from '@/components/permissions/composables/usePermissionRows'
import { usePermissionSave } from '@/components/permissions/composables/usePermissionSave'
import ObjectScopedPermissionsTable from '@/components/permissions/ObjectScopedPermissionsTable.vue'
import PermissionChangesConfirmModal from '@/components/permissions/PermissionChangesConfirmModal.vue'
import PermissionMatrixInfo from '@/components/permissions/PermissionMatrixInfo.vue'
import PermissionMatrixRow from '@/components/permissions/PermissionMatrixRow.vue'
import PermissionModalCreate from '@/components/permissions/PermissionModalCreate.vue'
import PermissionSelector from '@/components/permissions/PermissionSelector.vue'
import SaveProgressModal from '@/components/permissions/SaveProgressModal.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import UnsavedChangesModal from '@/components/UnsavedChangesModal.vue'
import backend from '@/services'
import { checkObjectPermissions, usePermissionRefs } from '@/utils/dataUtils'

const toast = useToast()
const { t } = useI18n()

const props = defineProps({
  entityId: { type: String, required: true },
  entityType: { type: String, required: true },
  objectLabelResolver: { type: Function, default: null },
  readonly: Boolean,
})

const permissionRefs = usePermissionRefs()
const permissions = ref([])
const objectModelQuery = ref('')
const onlyWithPermissions = ref(false)
const isLoading = ref(true)
const hasLoadedOnce = ref(false)
const showLoadingOverlay = ref(true)

const MIN_LOADING_TIME_MS = 400
let loadingStartTime = null
let loadingTimer = null

const pagination = ref({
  currentPage: 1,
  sortColumnKey: 'id',
  sortDirection: 'asc',
  perPage: 200,
})

const modals = {
  create: ref(false),
  confirm: ref(false),
  discardChanges: ref(false),
}

const lastRefresh = ref(null)

const formattedLastRefresh = computed(() => {
  if (!lastRefresh.value) return null
  return lastRefresh.value.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
})

async function fetchPermissions() {
  isLoading.value = true
  showLoadingOverlay.value = true
  loadingStartTime = Date.now()

  if (loadingTimer) {
    clearTimeout(loadingTimer)
    loadingTimer = null
  }

  try {
    const perPage = pagination.value.perPage
    const params = {
      limit: perPage,
      sort_by: pagination.value.sortColumnKey,
      sort_order: pagination.value.sortDirection,
      search_field: 'entity_id',
      search_value: props.entityId,
    }

    const first = await backend.objectPermissions.list({
      ...params,
      page: 1,
    })

    const totalPages = Math.ceil(first.pageDetails.totalCount / perPage)

    // Fetch remaining pages in parallel
    let allItems = first.items
    if (totalPages > 1) {
      const remaining = await Promise.all(
        Array.from({ length: totalPages - 1 }, (_, i) =>
          backend.objectPermissions.list({ ...params, page: i + 2 }),
        ),
      )
      allItems = allItems.concat(...remaining.map((r) => r.items))
    }

    permissions.value = allItems
    rebuild()
    lastRefresh.value = new Date()
    hasLoadedOnce.value = true
  } catch {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.permission.plural'),
      }),
    )
  } finally {
    isLoading.value = false

    // Ensure minimum loading time for reload overlay
    const elapsed = Date.now() - loadingStartTime
    const remaining = MIN_LOADING_TIME_MS - elapsed

    if (remaining > 0 && hasLoadedOnce.value) {
      loadingTimer = setTimeout(() => {
        showLoadingOverlay.value = false
      }, remaining)
    } else {
      showLoadingOverlay.value = false
    }
  }
}

const isInitialLoading = computed(
  () => showLoadingOverlay.value && !hasLoadedOnce.value,
)
const isReloading = computed(
  () => showLoadingOverlay.value && hasLoadedOnce.value,
)

const {
  isEditing,
  draft,
  hasChanges,
  startEdit,
  cancelEdit,
  rebuild,
  setGlobal,
  setGlobalCreate,
  setGlobalExtras,
  setObject,
  setObjectExtras,
  toUpsertsAndDeletes,
} = usePermissionDraft(permissions, props.entityId, props.entityType)

const {
  dataLoading,
  pendingChanges,
  performSave,
  saveProgress,
  closeProgressModal,
} = usePermissionSave(
  permissions,
  props.entityId,
  props.entityType,
  fetchPermissions,
  isEditing,
)

const {
  getObjectLabelSync,
  getObjectLabelSnapshot,
  prefetchObjectLabel,
  getObjectTypeLabel,
} = useObjectLabelCache(props.objectLabelResolver)

const { rows, allExpanded, toggleExpanded, toggleAll } = usePermissionRows(
  permissions,
  draft,
  props.entityId,
  props.entityType,
  isEditing,
  objectModelQuery,
  onlyWithPermissions,
  prefetchObjectLabel,
  getObjectLabelSnapshot,
  getObjectTypeLabel,
)

const { deselectAll, selectAll } = usePermissionBulkActions({
  isEditing,
  rows,
  setGlobal,
  setGlobalCreate,
  setGlobalExtras,
  setObject,
  setObjectExtras,
})

function showConfirmModal() {
  pendingChanges.value = toUpsertsAndDeletes()
  modals.confirm.value = true
}

function handleCancelClick() {
  if (hasChanges.value) {
    modals.discardChanges.value = true
  } else {
    cancelEdit()
  }
}

function confirmDiscard() {
  modals.discardChanges.value = false
  cancelEdit()
}

function cancelDiscard() {
  modals.discardChanges.value = false
}

function handleBeforeUnload(event) {
  if (isEditing.value && hasChanges.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}

watch(isEditing, (editing) => {
  if (editing) {
    onlyWithPermissions.value = false
    window.addEventListener('beforeunload', handleBeforeUnload)
  } else {
    window.removeEventListener('beforeunload', handleBeforeUnload)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  if (loadingTimer) {
    clearTimeout(loadingTimer)
  }
})

onMounted(async () => {
  fetchPermissions()

  await checkObjectPermissions(
    'object_permissions',
    props.objectId ?? props.entityId,
    permissionRefs,
    [],
    ['canCreate', 'canDelete'],
  )

  permissionRefs.canEdit = permissionRefs.canCreate && permissionRefs.canDelete
})
</script>

<template>
  <PermissionModalCreate
    v-model="modals.create.value"
    :entity-type="props.entityType"
    :entity-id="props.entityId"
    @confirmed="fetchPermissions"
  />

  <PermissionChangesConfirmModal
    v-model="modals.confirm.value"
    :changes="pendingChanges"
    :get-object-type-label="getObjectTypeLabel"
    :get-object-label-sync="getObjectLabelSync"
    @confirm="performSave"
  />

  <UnsavedChangesModal
    v-model="modals.discardChanges.value"
    @discard="confirmDiscard"
    @continue="cancelDiscard"
  />

  <SaveProgressModal
    v-model="saveProgress.isActive"
    :progress="saveProgress"
    @close="closeProgressModal"
  />

  <SectionTitleLineWithButton
    :icon="mdiKey"
    :title="$t('components.permissionMatrix.permissions')"
    :reload="fetchPermissions"
    :reload-disabled="isEditing"
    :reload-disabled-tooltip="
      t('components.permissionMatrix.reloadDisabledTooltip')
    "
  >
    <BaseButton
      color="dark"
      small
      :label="
        allExpanded
          ? t('components.permissionMatrix.collapseAll')
          : t('components.permissionMatrix.expandAll')
      "
      :icon="allExpanded ? mdiChevronUp : mdiChevronDown"
      @click="toggleAll"
    />

    <BaseButton
      v-if="!isEditing && permissionRefs.canEdit && !props.readonly"
      color="contrast"
      small
      :label="$t('common.edit')"
      :icon="mdiPencil"
      @click="startEdit"
    />

    <BaseButton
      v-if="isEditing"
      color="light"
      small
      :label="$t('components.permissionMatrix.deselectAll')"
      :icon="mdiCheckboxBlankOutline"
      @click="deselectAll"
    />

    <BaseButton
      v-if="isEditing"
      color="light"
      small
      :label="$t('components.permissionMatrix.selectAll')"
      :icon="mdiCheckboxMultipleMarked"
      @click="selectAll"
    />

    <BaseButton
      v-if="isEditing"
      color="dark"
      small
      :label="$t('common.cancel')"
      :icon="mdiCancel"
      @click="handleCancelClick"
    />

    <BaseButton
      v-if="isEditing"
      color="success"
      small
      :label="$t('common.save')"
      :disabled="!hasChanges"
      :icon="mdiContentSaveAll"
      @click="showConfirmModal"
    />

    <BaseButton
      v-if="permissionRefs.canCreate && !props.readonly"
      v-tooltip="
        isEditing ? t('components.permissionMatrix.editDisabledTooltip') : null
      "
      :icon="mdiPlus"
      :disabled="isEditing"
      color="success"
      rounded-full
      small
      @click="modals.create.value = true"
    />
  </SectionTitleLineWithButton>

  <PermissionMatrixInfo />

  <div class="w-full text-gray-900 dark:text-gray-100">
    <!-- Header (title & search) -->
    <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
      <!-- Data status -->
      <p class="text-sm text-gray-500 dark:text-gray-400">
        {{
          $t('components.permissionMatrix.dataStatus', {
            time: formattedLastRefresh ?? '--:--:--',
          })
        }}
      </p>

      <div class="flex items-center gap-3 min-w-0">
        <!-- Filter: only with permissions -->
        <label
          class="inline-flex items-center gap-2 text-sm select-none whitespace-nowrap"
          :class="
            isEditing
              ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed'
              : 'text-gray-600 dark:text-gray-400 cursor-pointer'
          "
        >
          <button
            type="button"
            role="switch"
            :aria-checked="onlyWithPermissions"
            :disabled="isEditing"
            class="relative inline-flex h-5 w-9 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-40 disabled:cursor-not-allowed"
            :class="
              onlyWithPermissions
                ? 'bg-blue-600'
                : 'bg-gray-300 dark:bg-gray-600'
            "
            @click="!isEditing && (onlyWithPermissions = !onlyWithPermissions)"
          >
            <span
              class="pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow ring-0 transition-transform duration-200 ease-in-out"
              :class="onlyWithPermissions ? 'translate-x-4' : 'translate-x-0'"
            />
          </button>
          {{ $t('components.permissionMatrix.onlyAssigned') }}
        </label>

        <!-- Search -->
        <div class="w-[360px] max-w-full min-w-0">
          <div class="relative">
            <input
              v-model="objectModelQuery"
              type="text"
              class="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 text-sm"
              :placeholder="
                $t('components.permissionMatrix.filterObjectModels')
              "
            />

            <button
              v-if="objectModelQuery"
              type="button"
              class="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-900 dark:hover:text-gray-100"
              @click="objectModelQuery = ''"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      class="relative overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
    >
      <table class="min-w-[860px] w-full text-sm table-fixed">
        <colgroup>
          <col class="w-[200px]" />

          <col />

          <col class="w-[170px]" />
        </colgroup>

        <thead
          class="bg-gray-50 dark:bg-gray-800 font-bold text-gray-900 dark:text-gray-100"
        >
          <tr class="text-left">
            <th class="px-4 py-3">
              {{ $t('components.permissionMatrix.objectModel') }}
            </th>

            <th class="px-4 py-3">
              {{ $t('components.permissionMatrix.globalPermission') }}
            </th>

            <th class="px-4 py-3 whitespace-nowrap">
              {{ $t('components.permissionMatrix.objectScoped') }}
            </th>
          </tr>
        </thead>

        <!-- Initial loading skeleton -->
        <tbody v-if="isInitialLoading">
          <tr
            v-for="i in 5"
            :key="'skeleton-' + i"
            class="border-t border-gray-200 dark:border-gray-700"
          >
            <td class="px-4 py-4">
              <div
                class="h-5 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
              />
            </td>

            <td class="px-4 py-4">
              <div class="flex gap-2">
                <div
                  class="h-9 w-20 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"
                />

                <div
                  class="h-9 w-20 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"
                />

                <div
                  class="h-9 w-24 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"
                />
              </div>
            </td>

            <td class="px-4 py-4">
              <div
                class="h-5 w-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
              />
            </td>
          </tr>
        </tbody>

        <!-- Data loaded -->
        <tbody v-else>
          <PermissionMatrixRow
            v-for="row in rows"
            :key="row.objectType"
            v-memo="[row.memoKey, isEditing]"
            :object-type="row.objectType"
            :object-entries="row.objectEntries"
            :expanded="row.expanded"
            :is-editing="isEditing"
            :get-object-type-label="getObjectTypeLabel"
            :object-entries-allowed="row?.allowedObjectKeys?.length > 0"
            @toggle-expanded="() => toggleExpanded(row.objectType)"
          >
            <template #global>
              <PermissionSelector
                mode="global"
                :model="row.objectType"
                :model-value="draft.global[row.objectType] ?? 'none'"
                :create-value="!!draft.globalCreate[row.objectType]"
                :extra-values="draft.extrasGlobal?.[row.objectType] ?? []"
                :disabled="!isEditing"
                :allowed-keys="row.allowedGlobalKeys"
                @update:model-value="(v) => setGlobal(row.objectType, v)"
                @update:create-value="(v) => setGlobalCreate(row.objectType, v)"
                @update:extra-values="(v) => setGlobalExtras(row.objectType, v)"
              />
            </template>

            <template #expanded>
              <ObjectScopedPermissionsTable
                v-if="row.objectScopeAllowed"
                :object-type="row.objectType"
                :object-entries="row.objectEntries"
                :is-editing="isEditing"
                :get-object-label-sync="getObjectLabelSync"
                :get-object-type-label="getObjectTypeLabel"
                :get-level="(ot, id) => draft.objects[ot]?.[id] ?? 'none'"
                :get-extras="(ot, id) => draft.extrasObjects?.[ot]?.[id] ?? []"
                :allowed-keys="row.allowedObjectKeys"
                @set-level="
                  ({ objectType, objectId, level }) =>
                    setObject(objectType, objectId, level)
                "
                @set-extras="
                  ({ objectType, objectId, extras }) =>
                    setObjectExtras(objectType, objectId, extras)
                "
              />
            </template>
          </PermissionMatrixRow>

          <tr
            v-if="rows.length === 0 && !isReloading"
            class="border-t border-gray-200 dark:border-gray-700"
          >
            <td colspan="3" class="px-4 py-6 text-gray-500 dark:text-gray-400">
              {{ $t('common.noData') }}
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Reload overlay -->
      <transition name="fade-overlay">
        <div
          v-if="isReloading"
          class="absolute inset-0 bg-white/60 dark:bg-slate-900/60 backdrop-blur-[1px] flex items-center justify-center z-10 rounded-xl"
        >
          <div
            class="flex items-center gap-3 bg-white dark:bg-slate-800 px-4 py-2 rounded-lg shadow-lg"
          >
            <div
              class="w-5 h-5 border-2 border-gray-300 dark:border-slate-500 border-t-blue-500 rounded-full animate-spin"
            />

            <span class="text-sm text-gray-600 dark:text-slate-300">{{
              $t('components.permissionMatrix.refreshing')
            }}</span>
          </div>
        </div>
      </transition>
    </div>

    <p v-if="isEditing" class="mt-3 text-xs text-gray-500 dark:text-gray-400">
      {{ $t('components.permissionMatrix.editHint') }}
    </p>
  </div>
</template>

<style scoped>
/* Override global _table.css mobile card-layout for this matrix table */
:deep(table) thead {
  display: table-header-group;
}
:deep(table) tr {
  display: table-row;
  border-bottom-width: 0;
  max-width: none;
  position: static;
}
:deep(table) td {
  display: table-cell;
  text-align: left;
  overflow: visible;
}
:deep(table) td:before {
  display: none;
}
:deep(table) td:not(:first-child) {
  border-left-width: 1px;
}

/* Overlay fade transition */
.fade-overlay-enter-active,
.fade-overlay-leave-active {
  transition: opacity 0.2s ease;
}
.fade-overlay-enter-from,
.fade-overlay-leave-to {
  opacity: 0;
}
</style>
