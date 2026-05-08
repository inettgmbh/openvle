<script setup>
import PermissionSelector from '@/components/permissions/PermissionSelector.vue'

const props = defineProps({
  objectType: { type: String, required: true },
  objectEntries: { type: Array, default: () => [] },
  isEditing: { type: Boolean, default: false },

  getObjectLabelSync: { type: Function, required: true },
  getObjectTypeLabel: { type: Function, required: true },

  getLevel: { type: Function, required: true }, // (objectType, objectId) => 'none' | ...
  getExtras: { type: Function, required: true }, // (objectType, objectId) => string[]
  allowedKeys: { type: Array, default: null }, // keys allowed for object scope (per model)
})

const emit = defineEmits(['set-level', 'set-extras'])

function setLevel(objectId, level) {
  emit('set-level', {
    objectType: props.objectType,
    objectId,
    level,
  })
}

function setExtras(objectId, extras) {
  emit('set-extras', {
    objectType: props.objectType,
    objectId,
    extras,
  })
}
</script>

<template>
  <div class="flex items-center justify-between gap-3 mb-3">
    <div class="font-bold text-gray-900 dark:text-gray-100">
      {{ $t('components.objectScopedPermissions.title') }}
    </div>

    <div class="text-xs text-gray-500 dark:text-gray-400">
      {{ $t('components.objectScopedPermissions.subtitle') }}
    </div>
  </div>

  <div
    class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
  >
    <table class="min-w-[820px] w-full text-sm">
      <thead class="bg-gray-50 dark:bg-gray-800 font-bold">
        <tr class="text-left">
          <th class="px-4 py-2 text-gray-900 dark:text-gray-100">
            {{ $t('common.object') }}
          </th>

          <th class="px-4 py-2 text-gray-900 dark:text-gray-100">
            {{ $t('components.objectScopedPermissions.permission') }}
          </th>

          <th
            class="px-4 py-2 w-[1%] whitespace-nowrap text-gray-900 dark:text-gray-100"
          >
            {{ $t('components.objectScopedPermissions.action') }}
          </th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="entry in objectEntries"
          :key="entry.objectId"
          class="border-t border-gray-200 dark:border-gray-700"
        >
          <td class="px-4 py-3">
            <div class="font-medium text-gray-900 dark:text-gray-100">
              {{ getObjectLabelSync(objectType, entry.objectId) }}
            </div>

            <div class="text-xs text-gray-500 dark:text-gray-400 font-mono">
              {{ entry.objectId }}
            </div>
          </td>

          <td class="px-4 py-3">
            <PermissionSelector
              mode="object"
              :model="objectType"
              :model-value="getLevel(objectType, entry.objectId)"
              :disabled="!isEditing"
              :allowed-keys="allowedKeys"
              :extra-values="getExtras(objectType, entry.objectId)"
              @update:model-value="(v) => setLevel(entry.objectId, v)"
              @update:extra-values="(v) => setExtras(entry.objectId, v)"
            />
          </td>

          <td class="px-4 py-3 whitespace-nowrap">
            <button
              type="button"
              class="px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 text-sm hover:bg-gray-50 dark:hover:bg-gray-800 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 disabled:opacity-50"
              :disabled="
                !isEditing ||
                (getLevel(objectType, entry.objectId) === 'none' &&
                  (getExtras(objectType, entry.objectId) ?? []).length === 0)
              "
              @click="
                (setLevel(entry.objectId, 'none'),
                setExtras(entry.objectId, []))
              "
            >
              {{ $t('components.objectScopedPermissions.remove') }}
            </button>
          </td>
        </tr>

        <tr
          v-if="objectEntries.length === 0"
          class="border-t border-gray-200 dark:border-gray-700"
        >
          <td colspan="3" class="px-4 py-3 text-gray-500 dark:text-gray-400">
            {{ $t('components.objectScopedPermissions.noObjectPermissions') }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
