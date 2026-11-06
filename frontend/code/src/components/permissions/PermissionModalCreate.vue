<script setup>
import {
  mdiAccount,
  mdiAccountMultipleOutline,
  mdiApplicationBrackets,
  mdiApps,
  mdiCalendarOutline,
  mdiCheckAll,
  mdiDomain,
  mdiFileDocumentMultiple,
  mdiFileSign,
  mdiMailboxOutline,
  mdiMonitor,
  mdiRemoteDesktop,
  mdiSchoolOutline,
  mdiVectorArrangeAbove,
} from '@mdi/js'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'vue-toastification'

import BaseButton from '@/components/BaseButton.vue'
import BaseButtons from '@/components/BaseButtons.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import CardBox from '@/components/CardBox.vue'
import CardBoxComponentFooter from '@/components/CardBoxComponentFooter.vue'
import CardBoxModal from '@/components/CardBoxModal.vue'
import FormDropdownPrefix from '@/components/FormDropdownPrefix.vue'
import FormField from '@/components/FormField.vue'
import SearchControl from '@/components/SearchControl.vue'
import backend from '@/services'
import { getObjectPermissionsOptions } from '@/utils/objectModelPermissions'
import { useAutofocusInput } from '@/utils/useAutofocusInput'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  entityId: {
    type: String,
    required: true,
  },
  entityType: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue', 'confirmed'])

const loading = ref(false)
const modalVisible = ref(props.modelValue)
const objectPermissionsOptions = computed(() =>
  getObjectPermissionsOptions(addPermissionObject.value.objectType),
)
const searchControlUserRef = ref(null)
const toast = useToast()
const { t } = useI18n()

const { autoFocusInputRef } = useAutofocusInput(modalVisible)

const addPermissionObject = ref({
  entityId: computed(() => props.entityId).value,
  entityType: computed(() => props.entityType).value,
  permissionKey: '',
  objectId: '',
  objectType: 'Application',
})

const addPermissionOptions = computed(() => [
  {
    label: t('components.permissionModalCreate.optionApplications'),
    value: 'Application',
    icon: mdiApps,
    fetchData: backend.applications.search,
    fetchSelected: backend.applications.getName,
    placeholder: t('components.permissionModalCreate.placeholderApplications'),
  },
  {
    label: t('components.permissionModalCreate.optionUsers'),
    value: 'User',
    icon: mdiAccount,
    fetchData: backend.users.search,
    fetchSelected: backend.users.formatById,
    placeholder: t('components.permissionModalCreate.placeholderUsers'),
  },
  {
    label: t('components.permissionModalCreate.optionOs'),
    value: 'OS',
    icon: mdiApplicationBrackets,
    fetchData: backend.os.search,
    fetchSelected: backend.os.getName,
    placeholder: t('components.permissionModalCreate.placeholderOs'),
  },
  {
    label: t('components.permissionModalCreate.optionDocuments'),
    value: 'Document',
    icon: mdiFileDocumentMultiple,
    fetchData: backend.documents.search,
    fetchSelected: backend.documents.getName,
    placeholder: t('components.permissionModalCreate.placeholderDocuments'),
  },
  {
    label: t('components.permissionModalCreate.optionMailTemplates'),
    value: 'MailTemplate',
    icon: mdiMailboxOutline,
    fetchData: backend.mailTemplates.search,
    fetchSelected: backend.mailTemplates.getName,
    placeholder: t('components.permissionModalCreate.placeholderMailTemplates'),
  },
  {
    label: t('components.permissionModalCreate.optionVendors'),
    value: 'Vendor',
    icon: mdiDomain,
    fetchData: backend.vendors.search,
    fetchSelected: backend.vendors.getName,
    placeholder: t('components.permissionModalCreate.placeholderVendors'),
  },
  {
    label: t('components.permissionModalCreate.optionPolicies'),
    value: 'Policy',
    icon: mdiFileSign,
    fetchData: backend.policies.search,
    fetchSelected: backend.policies.getName,
    placeholder: t('components.permissionModalCreate.placeholderPolicies'),
  },
  {
    label: t('components.permissionModalCreate.optionRoles'),
    value: 'Role',
    icon: mdiAccountMultipleOutline,
    fetchData: backend.roles.search,
    fetchSelected: backend.roles.getName,
    placeholder: t('components.permissionModalCreate.placeholderRoles'),
  },
  {
    label: t('components.permissionModalCreate.optionCourses'),
    value: 'Course',
    icon: mdiSchoolOutline,
    fetchData: backend.courses.search,
    fetchSelected: backend.courses.getName,
    placeholder: t('components.permissionModalCreate.placeholderCourses'),
  },
  {
    label: t('components.permissionModalCreate.optionEvents'),
    value: 'Event',
    icon: mdiCalendarOutline,
    fetchData: backend.events.search,
    fetchSelected: backend.events.getName,
    placeholder: t('components.permissionModalCreate.placeholderEvents'),
  },
  {
    label: t('components.permissionModalCreate.optionGuacamole'),
    value: 'Guacamole',
    icon: mdiRemoteDesktop,
    fetchData: backend.guacamole.search,
    fetchSelected: backend.guacamole.getName,
    placeholder: t('components.permissionModalCreate.placeholderGuacamole'),
  },
  {
    label: t('components.permissionModalCreate.optionTemplates'),
    value: 'Template',
    icon: mdiVectorArrangeAbove,
    fetchData: backend.templates.search,
    fetchSelected: backend.templates.getName,
    placeholder: t('components.permissionModalCreate.placeholderTemplates'),
  },
  {
    label: t('components.permissionModalCreate.optionVms'),
    value: 'VirtualMachine',
    icon: mdiMonitor,
    fetchData: backend.vms.search,
    fetchSelected: backend.vms.getName,
    placeholder: t('components.permissionModalCreate.placeholderVms'),
  },
])

const onFormSubmit = () => {
  emit('confirmed', addPermissionObject.value)
  emit('update:modelValue', false)
}

const resetAddPermissionForm = () => {
  addPermissionObject.value.permissionKey = ''
  addPermissionObject.value.objectId = ''
  addPermissionObject.value.objectType = 'Application'
  searchControlUserRef.value?.setInitialDisplay('')
  searchControlUserRef.value?.setSelectedId('')
}

const submitEnabled = computed(() => {
  return addPermissionObject.value.permissionKey &&
    addPermissionObject.value.objectId
    ? true
    : false
})

async function addObjectPermission() {
  try {
    await backend.objectPermissions.create({
      objectType: addPermissionObject.value.objectType,
      objectId: addPermissionObject.value.objectId,
      entityId: addPermissionObject.value.entityId,
      entityType: addPermissionObject.value.entityType,
      permissionKey: addPermissionObject.value.permissionKey,
    })
    toast.success(t('components.permissionModalCreate.permissionAdded'))
  } catch (error) {
    toast.error(
      `${t('common.addError', { entity: t('objectTypes.permission.singular') })}\n${error?.response?.data?.detail}`,
      { timeout: 8400 },
    )
  } finally {
    resetAddPermissionForm()
    onFormSubmit()
  }
}

watch(
  () => modalVisible.value,
  (newVal) => {
    emit('update:modelValue', newVal)
  },
)

watch(
  () => props.modelValue,
  (newVal) => {
    modalVisible.value = newVal
  },
)

watch(
  () => addPermissionObject.value.objectType,
  () => {
    addPermissionObject.value.objectId = null
    addPermissionObject.value.permissionKey = ''
    searchControlUserRef.value?.setInitialDisplay('')
    searchControlUserRef.value?.setSelectedId('')
  },
)
</script>

<template>
  <CardBoxModal
    v-model="modalVisible"
    :has-button="false"
    :title="$t('components.permissionModalCreate.createObjectPermission')"
    custom-class="z-50 w-full md:w-4/5 lg:w-3/5 xl:w-fit !w-[50vw]"
    has-search
    @cancel="resetAddPermissionForm()"
  >
    <template v-if="loading">
      <div class="flex flex-col justify-center items-center min-h-[300px]">
        <svg
          class="animate-spin h-10 w-10 text-warning"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>

          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v8H4z"
          ></path>
        </svg>

        <p class="mt-4 text-warning">
          {{ t('components.permissionModalCreate.loading') }}
        </p>
      </div>
    </template>

    <template v-else>
      <CardBox class="grid mb-6">
        <!-- Entity type and id selection (user or role)-->
        <FormField :label="$t('components.permissionModalCreate.objectSelect')">
          <div class="flex">
            <FormDropdownPrefix
              v-model:prefix-value="addPermissionObject.objectType"
              :options="addPermissionOptions"
              required
            />

            <div class="flex-1">
              <SearchControl
                v-model="addPermissionObject.objectId"
                borders="right"
                :fetch-data="
                  addPermissionOptions.find(
                    (option) => option.value === addPermissionObject.objectType,
                  )?.fetchData ?? null
                "
                :fetch-selected="
                  addPermissionOptions.find(
                    (option) => option.value === addPermissionObject.objectType,
                  )?.fetchSelected ?? null
                "
                :placeholder="
                  addPermissionOptions.find(
                    (option) => option.value === addPermissionObject.objectType,
                  )?.placeholder ?? null
                "
                required
                @set-ref="
                  (ref) => {
                    searchControlUserRef = ref
                    autoFocusInputRef = ref
                  }
                "
              />
            </div>
          </div>
        </FormField>

        <BaseDivider />

        <!-- Permission selection (read, update, delete, full or actions)-->
        <FormField :label="$t('components.permissionModalCreate.permission')">
          <div class="space-y-2">
            <label
              v-for="option in objectPermissionsOptions"
              :key="option.value"
              class="flex items-start gap-3 p-2 rounded-lg cursor-pointer border border-transparent hover:border-gray-200"
              :class="
                addPermissionObject.permissionKey === option.value
                  ? 'bg-gray-800 text-white dark:bg-gray-700 border-gray-200'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-800'
              "
            >
              <input
                v-model="addPermissionObject.permissionKey"
                type="radio"
                class="mt-1 form-radio"
                :value="option.value"
                required
              />

              <div class="leading-tight">
                <div class="text-sm font-medium">{{ option.label }}</div>

                <div
                  v-if="option.description"
                  class="text-xs mt-0.5"
                  :class="
                    addPermissionObject.permissionKey === option.value
                      ? 'bg-gray-800 text-white dark:bg-gray-700 border-gray-200'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                  "
                >
                  {{ option.description }}
                </div>
              </div>
            </label>
          </div>
        </FormField>

        <BaseDivider />

        <CardBoxComponentFooter>
          <BaseButtons>
            <BaseButton
              :label="$t('common.create')"
              type="submit"
              :icon="mdiCheckAll"
              color="success"
              :disabled="!submitEnabled"
              @click="addObjectPermission"
            />

            <BaseButton
              type="reset"
              color="success"
              :label="$t('common.cancel')"
              outline
              @click="modalVisible = false"
            />
          </BaseButtons>
        </CardBoxComponentFooter>
      </CardBox>
    </template>
  </CardBoxModal>
</template>

<style scoped>
ul {
  list-style: disc;
  padding-left: 1.25rem;
}
li {
  margin-bottom: 0.5rem;
}
</style>
