<script setup>
import {
  mdiAlertOutline,
  mdiCalendarClock,
  mdiCheckCircleOutline,
  mdiCloseCircleOutline,
  mdiCog,
  mdiDatabase,
  mdiDownload,
  mdiInformation,
  mdiPencil,
  mdiUpdate,
  mdiVariable,
} from '@mdi/js'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import BaseMarkdown from '@/components/BaseMarkdown.vue'
import BaseTable from '@/components/BaseTable.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormControl from '@/components/FormControl.vue'
import FormField from '@/components/FormField.vue'
import NotificationBar from '@/components/NotificationBar.vue'
import PillTag from '@/components/PillTag.vue'
import SectionMain from '@/components/SectionMain.vue'
import SectionTitleLineWithButton from '@/components/SectionTitleLineWithButton.vue'
import { SearchOperators } from '@/components/Tables/searchOperators'
import { FIELD_LIMITS } from '@/config/fieldLimits'
import LayoutAuthenticated from '@/layouts/LayoutAuthenticated.vue'
import backend from '@/services'
import { useMainStore } from '@/stores/main'
import {
  checkObjectPermissions,
  exportJsonFile,
  formatDate,
  formatSettingValue,
  formatSystemSettingVisibility,
  getHTMLInputType,
  getUserLink,
  resolveFieldFromLookup,
  usePermissionRefs,
  valueValidator,
  visibilitySystemSettingFilter,
} from '@/utils/dataUtils.js'
import { systemSettingVisibilityIcon } from '@/utils/icons'
import { visibilityColorSystemSetting } from '@/utils/objectColors'
import { usePaginationList } from '@/utils/pagination'
import { systemSettingVisibilityTooltip } from '@/utils/tooltips'

const { t } = useI18n()
const permissionRefs = usePermissionRefs()
const toast = useToast()

const mainStore = useMainStore()
const objects = ref([])
const objSingle = ref([])
const permissionsLoaded = ref(false)

/* PAGINATION ONLY */
const dataLoading = ref(true)
const modals = {
  viewSetting: ref(false),
  editSetting: ref(false),
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
  initialPerPage: 100,
  initialSortColumn: 'key',
  initialSortOrder: 'asc',
  initialSearchField: null,
  initialSearchValue: null,
  fetch: fetchObjects,
  useReplace: true,
  syncQuery: true,
})

const isInternalSetting = computed(
  () => objSingle.value?.visibility === 'internal',
)

const booleanDisplayValue = computed(
  () => String(objSingle.value?.value).toLowerCase() === 'true',
)

const canEditSetting = computed(
  () => permissionRefs.canEdit === true && !isInternalSetting.value,
)

const openViewModal = (systemSetting) => {
  objSingle.value = {
    ...objects.value.find((object) => object.id === systemSetting.id),
  }
  objSingle.value.inputType = getHTMLInputType(
    objSingle.value.type,
    objSingle.value.value,
  )
  modals.viewSetting.value = true
}

const openEditModal = (systemSetting) => {
  objSingle.value = {
    ...objects.value.find((object) => object.id === systemSetting.id),
  }
  objSingle.value.inputType = getHTMLInputType(
    objSingle.value.type,
    objSingle.value.value,
  )

  // Redirect to view modal for internal settings
  if (objSingle.value.visibility === 'internal') {
    modals.viewSetting.value = true
    return
  }

  modals.editSetting.value = true
}

const switchToEdit = () => {
  modals.viewSetting.value = false
  setTimeout(() => {
    modals.editSetting.value = true
  }, 160)
}
/**/

async function editSetting(systemSettingId, systemSettingValue) {
  try {
    systemSettingValue = formatSettingValue(
      objSingle.value.type,
      systemSettingValue,
    )

    await backend.system.update(systemSettingId, systemSettingValue)
    fetchObjects()
    toast.success(
      t('common.editSuccess', {
        entity: t('objectTypes.systemSetting.singular'),
      }),
    )
    mainStore.loadSettings()
  } catch (error) {
    toast.error(
      `${t('views.system.settings.editError')}\n${error?.response?.data?.detail || error?.message}`,
      { timeout: 8400 },
    )
  } finally {
    resetForms()
  }
}

async function fetchObjects() {
  try {
    dataLoading.value = true

    const response = await backend.system.list({
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
      { from: 'updatedById', to: 'updatedBy', keyspace: 'users' },
    ])
  } catch (error) {
    toast.error(
      t('common.loadErrorPlural', {
        entities: t('objectTypes.systemSetting.plural'),
      }),
    )
  } finally {
    dataLoading.value = false
  }
}

const resetForms = () => {
  objSingle.value = ''
}

const tableButtons = computed(() => {
  if (permissionRefs.canEdit === true) return ['view', 'edit']
  return ['view']
})

const settingUpdatable = computed(() => {
  /** Check whether the required fields are present */
  if (
    !objSingle.value.id ||
    !objSingle.value.key ||
    (!objSingle.value.value && objSingle.value.inputType != 'number')
  ) {
    return false
  }

  /** Check whether the required fields contain data */
  if (
    objSingle.value.value &&
    objSingle.value.value.length <= 0 &&
    objSingle.value.inputType != 'number'
  ) {
    return false
  }

  /** Call the global `valueValidator` function and check if there is an error */
  const validationError = valueValidator(
    objSingle.value.value,
    objSingle.value.type,
  )
  if (validationError !== true) {
    return false
  }

  return true
})

const handleExport = async () => {
  try {
    await exportJsonFile(objects.value, 'system-settings')
  } catch (err) {
    toast.error(`${t('views.system.settings.exportError')}\n${err}`, {
      timeout: 8400,
    })
  }
}

const searchBarFields = [
  {
    preset: 'key',
    label: t('views.system.settings.setting'),
    operators: SearchOperators.CONTAINS_ONLY,
  },
  {
    key: 'value',
    label: t('common.value'),
    icon: mdiVariable,
    operators: SearchOperators.CONTAINS_ONLY,
  },
  {
    preset: 'visibility',
    operators: SearchOperators.EQUALS_ONLY_ONLY,
    options: visibilitySystemSettingFilter(),
  },
  { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
  { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
]

onMounted(async () => {
  initialFetch()
  await checkObjectPermissions(
    'system',
    '*',
    permissionRefs,
    [
      {
        key: 'canEdit',
        objectType: 'system',
        objectPermission: 'update',
        objectPath: '/*',
      },
    ],
    [],
  )

  permissionsLoaded.value = true
})
</script>

<template>
  <LayoutAuthenticated>
    <!-- Modal: View setting (read-only detail) -->
    <CardBoxModal
      :key="'view-' + objSingle.id"
      v-model="modals.viewSetting.value"
      :title="$t('views.system.settings.viewTitle')"
      :has-button="false"
      :has-cancel="false"
      custom-class="md:!w-4/5 lg:!w-3/5 xl:!w-1/2"
      @cancel="resetForms()"
    >
      <div class="space-y-5">
        <!-- Setting name -->
        <div>
          <p
            class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-slate-400 mb-1"
          >
            {{ $t('views.system.settings.setting') }}
          </p>

          <div class="flex items-center gap-2">
            <BaseIcon
              :path="mdiCog"
              :size="20"
              class="text-gray-500 dark:text-slate-400"
            />

            <span
              class="font-mono text-base font-semibold text-gray-900 dark:text-slate-100"
            >
              {{ objSingle.key }}
            </span>
          </div>
        </div>

        <!-- Description -->
        <div v-if="objSingle.description">
          <p
            class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-slate-400 mb-1"
          >
            {{ $t('common.description') }}
          </p>

          <BaseMarkdown v-model="objSingle.description" action="view" />
        </div>

        <!-- Data type and visibility -->
        <div class="flex flex-wrap items-center gap-4">
          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-slate-400 mb-1"
            >
              {{ $t('views.system.settings.dataType') }}
            </p>

            <div class="flex items-center gap-1.5">
              <BaseIcon
                :path="mdiVariable"
                :size="18"
                class="text-gray-500 dark:text-slate-400"
              />

              <span class="text-sm text-gray-700 dark:text-slate-300">
                {{ objSingle.type }}
              </span>
            </div>
          </div>

          <div>
            <p
              class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-slate-400 mb-1"
            >
              {{ $t('views.system.settings.visibility') }}
            </p>

            <PillTag
              :label="formatSystemSettingVisibility(objSingle.visibility)"
              :color="visibilityColorSystemSetting(objSingle.visibility)"
              :icon="systemSettingVisibilityIcon(objSingle.visibility)"
              :disabled="true"
              small
            />
          </div>
        </div>

        <!-- Value -->
        <div>
          <p
            class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-slate-400 mb-1"
          >
            {{ $t('common.value') }}
          </p>

          <div
            class="rounded-lg border border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-800/50 px-4 py-3"
          >
            <div
              v-if="objSingle.inputType === 'boolean'"
              class="flex items-center gap-2"
            >
              <BaseIcon
                :path="
                  booleanDisplayValue
                    ? mdiCheckCircleOutline
                    : mdiCloseCircleOutline
                "
                :size="20"
                :class="
                  booleanDisplayValue
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-red-500 dark:text-red-400'
                "
              />

              <span class="text-sm text-gray-900 dark:text-slate-100">
                {{
                  booleanDisplayValue
                    ? $t('common.active') + ' (true)'
                    : $t('common.inactive') + ' (false)'
                }}
              </span>
            </div>

            <span
              v-else
              class="font-mono text-sm text-gray-900 dark:text-slate-100 break-all"
            >
              {{ objSingle.value }}
            </span>
          </div>
        </div>

        <!-- Audit trail -->
        <div
          class="pt-3 border-t border-gray-200 dark:border-slate-700 space-y-1.5"
        >
          <div
            v-if="objSingle.updatedAt"
            class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-slate-400"
          >
            <BaseIcon :path="mdiCalendarClock" :size="14" />

            <span
              >{{ $t('views.system.settings.lastChange') }}:
              {{ formatDate(objSingle.updatedAt) }}</span
            >
          </div>

          <div
            v-if="objSingle.updatedBy"
            class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-slate-400"
          >
            <BaseIcon :path="mdiUpdate" :size="14" />

            <span>
              {{ $t('views.system.settings.changedBy') }}:
              <router-link
                v-if="getUserLink(objSingle.updatedBy, objSingle.updatedById)"
                :to="getUserLink(objSingle.updatedBy, objSingle.updatedById)"
                class="underline hover:text-gray-700 dark:hover:text-slate-200"
              >
                {{ objSingle.updatedBy }}
              </router-link>

              <template v-else>{{ objSingle.updatedBy }}</template>
            </span>
          </div>
        </div>

        <!-- Edit button -->
        <div v-if="canEditSetting" class="pt-2">
          <BaseButton
            :icon="mdiPencil"
            :label="$t('common.edit')"
            color="info"
            small
            outline
            @click="switchToEdit()"
          />
        </div>
      </div>
    </CardBoxModal>

    <!-- Modal: Edit setting -->
    <CardBoxModal
      :key="'edit-' + objSingle.id"
      v-model="modals.editSetting.value"
      button="warning"
      :button-label="$t('views.system.settings.change')"
      :title="$t('views.system.settings.editTitle')"
      has-cancel
      :disabled="!settingUpdatable"
      custom-class="md:!w-4/5 lg:!w-3/5 xl:!w-1/2"
      @cancel="resetForms()"
      @form-submitted="editSetting(objSingle.id, objSingle.value)"
    >
      <div class="edit-setting-form space-y-4">
        <!-- Context header -->
        <div
          class="flex flex-wrap items-center gap-3 pb-3 border-b border-gray-200 dark:border-slate-700"
        >
          <span
            class="font-mono text-sm font-semibold text-gray-900 dark:text-slate-100"
          >
            {{ objSingle.key }}
          </span>

          <span
            class="text-xs text-gray-500 dark:text-slate-400 flex items-center gap-1"
          >
            <BaseIcon
              :path="mdiVariable"
              :size="14"
              class="text-gray-400 dark:text-slate-500"
            />
            {{ objSingle.type }}
          </span>

          <PillTag
            :label="formatSystemSettingVisibility(objSingle.visibility)"
            :color="visibilityColorSystemSetting(objSingle.visibility)"
            :icon="systemSettingVisibilityIcon(objSingle.visibility)"
            :disabled="true"
            small
          />
        </div>

        <!-- Description -->
        <div v-if="objSingle.description">
          <BaseMarkdown v-model="objSingle.description" action="view" />
        </div>

        <!-- Compact warning -->
        <div
          class="flex items-start gap-2 rounded-lg border border-amber-300 dark:border-amber-600 bg-amber-50 dark:bg-amber-950/30 px-3 py-2.5"
        >
          <BaseIcon
            :path="mdiAlertOutline"
            :size="18"
            class="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5"
          />

          <p class="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
            <b>{{ $t('views.system.settings.warningBold') }}</b>
            {{ $t('views.system.settings.warningText') }}
          </p>
        </div>

        <!-- Value field -->
        <FormField
          :label="$t('common.value')"
          :help="$t('views.system.settings.valueHelp')"
        >
          <div>
            <!-- Non-boolean -->
            <FormControl
              v-if="objSingle.inputType !== 'boolean'"
              v-model="objSingle.value"
              :maxlength="FIELD_LIMITS.system.value"
              :icon="mdiDatabase"
              :type="objSingle.inputType"
              :validate="(val) => valueValidator(val, objSingle.type)"
              :step="objSingle.type == 'float' ? 0.0001 : 1"
              required
            />

            <!-- Boolean toggle buttons -->
            <div v-else class="flex gap-3">
              <button
                type="button"
                class="flex-1 flex items-center justify-center gap-2.5 rounded-lg border-2 px-5 py-3.5 text-base font-medium transition-colors"
                :class="
                  booleanDisplayValue
                    ? 'border-emerald-500 dark:border-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300'
                    : 'border-gray-200 dark:border-slate-600 text-gray-500 dark:text-slate-400 hover:border-gray-300 dark:hover:border-slate-500'
                "
                @click="objSingle.value = 'true'"
              >
                <BaseIcon :path="mdiCheckCircleOutline" :size="22" />
                {{ $t('common.active') }}
              </button>

              <button
                type="button"
                class="flex-1 flex items-center justify-center gap-2.5 rounded-lg border-2 px-5 py-3.5 text-base font-medium transition-colors"
                :class="
                  !booleanDisplayValue
                    ? 'border-red-500 dark:border-red-400 bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300'
                    : 'border-gray-200 dark:border-slate-600 text-gray-500 dark:text-slate-400 hover:border-gray-300 dark:hover:border-slate-500'
                "
                @click="objSingle.value = 'false'"
              >
                <BaseIcon :path="mdiCloseCircleOutline" :size="22" />
                {{ $t('common.inactive') }}
              </button>
            </div>
          </div>
        </FormField>
      </div>
    </CardBoxModal>

    <SectionMain>
      <SectionTitleLineWithButton
        :icon="mdiCog"
        :title="$t('routes.settingsList')"
        main
        docs-path="/docs/usage/openvle/system/settings/"
        :reload="fetchObjects"
      >
        <BaseButton
          :icon="mdiDownload"
          :label="$t('common.export')"
          color="contrast"
          rounded-full
          small
          @click="handleExport"
        />
      </SectionTitleLineWithButton>

      <NotificationBar :dismissable="false" color="info" :icon="mdiInformation">
        <b>{{ $t('views.system.settings.infoNotice') }}</b>
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
          :created-column-enabled="false"
          object-model="settings"
          :buttons="tableButtons"
          :emit-edit-object="true"
          :emit-view-object="true"
          :search-bar-fields="searchBarFields"
          :search-bar-max-filters="1"
          :columns="[
            {
              key: 'key',
              label: $t('views.system.settings.setting'),
              sortable: true,
              width: '250px',
            },
            {
              key: 'value',
              label: $t('common.value'),
              sortable: true,
              width: '280px',
              formatter: (val) => {
                if (val === 'true') return $t('common.active')
                if (val === 'false') return $t('common.inactive')
                return String(val)
              },
            },
            {
              label: $t('views.system.settings.visibility'),
              key: 'visibility',
              color: visibilityColorSystemSetting,
              tooltip: (value) => systemSettingVisibilityTooltip(value),
              icon: (value) => systemSettingVisibilityIcon(value),
              formatter: ['', ''],
              filters: visibilitySystemSettingFilter(),
              width: '140px',
            },
            {
              key: 'updatedAt',
              label: $t('views.system.settings.changedAt'),
              sortable: true,
              class: 'text-gray-500 dark:text-slate-400 text-sm',
              formatter: (val) => {
                return formatDate(val)
              },
              width: '190px',
            },
          ]"
          @view-object="(obj) => openViewModal(obj)"
          @edit-object="(obj) => openEditModal(obj)"
          @search-triggered="handleSearch"
          @sort-order-changed="handleSortOrderChanged"
          @pagination-changed="handlePaginationChanged"
        />
      </CardBox>
    </SectionMain>
  </LayoutAuthenticated>
</template>

<style scoped>
.edit-setting-form :deep(input),
.edit-setting-form :deep(select) {
  height: 3.5rem;
  font-size: 1rem;
}
</style>
