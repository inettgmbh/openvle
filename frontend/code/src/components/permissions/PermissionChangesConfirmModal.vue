<script setup>
import { mdiAlert, mdiCheck, mdiClose, mdiDelete, mdiPlus } from '@mdi/js'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/BaseButton.vue'
import CardBox from '@/components/CardBox.vue'
import OverlayLayer from '@/components/OverlayLayer.vue'
import { getObjectPermissionShortLabel } from '@/utils/objectModelPermissions'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  changes: { type: Object, required: true },
  getObjectTypeLabel: { type: Function, required: true },
  getObjectLabelSync: { type: Function, required: true },
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const hasChanges = computed(() => {
  return props.changes.upserts.length > 0 || props.changes.deletes.length > 0
})

const groupedChanges = computed(() => {
  const groups = {}

  // Group upserts by object type
  for (const upsert of props.changes.upserts) {
    const ot = upsert.object_type
    if (!groups[ot]) {
      groups[ot] = {
        label: props.getObjectTypeLabel(ot),
        upserts: [],
        deletes: [],
      }
    }
    groups[ot].upserts.push(upsert)
  }

  // Group deletes by object type
  for (const del of props.changes.deletes) {
    const ot = del.object_type
    if (!groups[ot]) {
      groups[ot] = {
        label: props.getObjectTypeLabel(ot),
        upserts: [],
        deletes: [],
      }
    }
    groups[ot].deletes.push(del)
  }

  return Object.entries(groups)
    .sort(([, a], [, b]) => a.label.localeCompare(b.label, 'de'))
    .map(([objectType, data]) => ({ objectType, ...data }))
})

function formatPermissionKey(key, model) {
  return getObjectPermissionShortLabel({ permission: key, model }) || key
}

function getChangeDescription(change, isUpsert) {
  const scope =
    change.object_id == null
      ? t('components.permissionChangesConfirm.global')
      : props.getObjectLabelSync(change.object_type, change.object_id)
  const permission = formatPermissionKey(
    change.permission_key || change.previous,
    change?.object_type,
  )

  return { scope, permission }
}

function cancel() {
  emit('update:modelValue', false)
  emit('cancel')
}

function confirm() {
  emit('update:modelValue', false)
  emit('confirm')
}
</script>

<template>
  <OverlayLayer v-show="modelValue" @overlay-click="cancel">
    <CardBox
      v-show="modelValue"
      class="shadow-lg max-h-modal w-11/12 md:w-3/5 lg:w-2/5 xl:w-4/12 z-50"
      is-modal
    >
      <div class="flex items-start justify-between mb-6">
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center"
          >
            <svg
              class="w-6 h-6 text-yellow-600 dark:text-yellow-400"
              :d="mdiAlert"
              viewBox="0 0 24 24"
            >
              <path fill="currentColor" :d="mdiAlert" />
            </svg>
          </div>

          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {{ $t('components.permissionChangesConfirm.confirmTitle') }}
            </h3>

            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ $t('components.permissionChangesConfirm.confirmSubtitle') }}
            </p>
          </div>
        </div>
      </div>

      <div v-if="!hasChanges" class="mb-6">
        <p class="text-gray-500 dark:text-gray-400">
          {{ $t('components.permissionChangesConfirm.noChanges') }}
        </p>
      </div>

      <div v-else class="mb-6 max-h-96 overflow-y-auto">
        <div
          v-for="group in groupedChanges"
          :key="group.objectType"
          class="mb-4 last:mb-0"
        >
          <h4 class="font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {{ group.label }}
          </h4>

          <!-- Neue Berechtigungen -->
          <div v-if="group.upserts.length > 0" class="mb-3">
            <div class="flex items-center gap-2 mb-2">
              <svg
                class="w-4 h-4 text-green-600 dark:text-green-400"
                :d="mdiPlus"
                viewBox="0 0 24 24"
              >
                <path fill="currentColor" :d="mdiPlus" />
              </svg>

              <span
                class="text-sm font-medium text-green-600 dark:text-green-400"
              >
                {{ $t('components.permissionChangesConfirm.added') }}
                ({{ group.upserts.length }})
              </span>
            </div>

            <ul class="space-y-1 ml-6">
              <li
                v-for="(upsert, idx) in group.upserts"
                :key="`upsert-${idx}`"
                class="text-sm text-gray-700 dark:text-gray-300"
              >
                <span class="font-medium"
                  >{{ getChangeDescription(upsert, true).scope }}:</span
                >
                {{ getChangeDescription(upsert, true).permission }}
              </li>
            </ul>
          </div>

          <!-- Entfernte Berechtigungen -->
          <div v-if="group.deletes.length > 0">
            <div class="flex items-center gap-2 mb-2">
              <svg
                class="w-4 h-4 text-red-600 dark:text-red-400"
                :d="mdiDelete"
                viewBox="0 0 24 24"
              >
                <path fill="currentColor" :d="mdiDelete" />
              </svg>

              <span class="text-sm font-medium text-red-600 dark:text-red-400">
                {{ $t('components.permissionChangesConfirm.removed') }}
                ({{ group.deletes.length }})
              </span>
            </div>

            <ul class="space-y-1 ml-6">
              <li
                v-for="(del, idx) in group.deletes"
                :key="`delete-${idx}`"
                class="text-sm text-gray-700 dark:text-gray-300"
              >
                <span class="font-medium"
                  >{{ getChangeDescription(del, false).scope }}:</span
                >
                {{
                  getChangeDescription(del, false).permission ||
                  $t('components.permissionChangesConfirm.allPermissions')
                }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div
        class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700"
      >
        <BaseButton
          color="dark"
          :label="$t('common.cancel')"
          :icon="mdiClose"
          @click="cancel"
        />

        <BaseButton
          color="success"
          :label="$t('components.permissionChangesConfirm.saveChanges')"
          :icon="mdiCheck"
          :disabled="!hasChanges"
          @click="confirm"
        />
      </div>
    </CardBox>
  </OverlayLayer>
</template>
