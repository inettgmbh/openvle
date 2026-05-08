<script setup>
import {
  mdiArrowRightBold,
  mdiAutoFix,
  mdiChevronDown,
  mdiCircleOpacity,
  mdiCogOutline,
  mdiEyeOutline,
  mdiInformationOutline,
  mdiPencilOutline,
  mdiPlusBoxOutline,
  mdiShieldCrownOutline,
  mdiStarCircleOutline,
  mdiTrashCanOutline,
} from '@mdi/js'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const isExpanded = ref(false)

const permissionLevels = computed(() => [
  {
    icon: mdiShieldCrownOutline,
    name: t('components.permissionMatrixInfo.levelFullAccess'),
    color: 'amber',
    description: t('components.permissionMatrixInfo.levelFullAccessDesc'),
  },
  {
    icon: mdiPlusBoxOutline,
    name: t('components.permissionMatrixInfo.levelCreate'),
    color: 'blue',
    description: t('components.permissionMatrixInfo.levelCreateDesc'),
  },
  {
    icon: mdiEyeOutline,
    name: t('components.permissionMatrixInfo.levelRead'),
    color: 'emerald',
    description: t('components.permissionMatrixInfo.levelReadDesc'),
  },
  {
    icon: mdiPencilOutline,
    name: t('components.permissionMatrixInfo.levelEdit'),
    color: 'emerald',
    description: t('components.permissionMatrixInfo.levelEditDesc'),
  },
  {
    icon: mdiTrashCanOutline,
    name: t('components.permissionMatrixInfo.levelDelete'),
    color: 'emerald',
    description: t('components.permissionMatrixInfo.levelDeleteDesc'),
  },
  {
    icon: mdiStarCircleOutline,
    name: t('components.permissionMatrixInfo.levelExtras'),
    color: 'violet',
    description: t('components.permissionMatrixInfo.levelExtrasDesc'),
  },
])

const behaviors = computed(() => [
  {
    icon: mdiArrowRightBold,
    title: t('components.permissionMatrixInfo.noteChain'),
    text: t('components.permissionMatrixInfo.noteChainDesc'),
  },
  {
    icon: mdiAutoFix,
    title: t('components.permissionMatrixInfo.noteAutoFull'),
    text: t('components.permissionMatrixInfo.noteAutoFullDesc'),
  },
  {
    icon: mdiCircleOpacity,
    title: t('components.permissionMatrixInfo.noteImplicit'),
    text: t('components.permissionMatrixInfo.noteImplicitDesc'),
  },
  {
    icon: mdiCogOutline,
    title: t('components.permissionMatrixInfo.noteOverrides'),
    text: t('components.permissionMatrixInfo.noteOverridesDesc'),
  },
])
</script>

<template>
  <div
    class="mb-4 rounded-xl border border-blue-200 dark:border-blue-900/50 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 overflow-hidden"
  >
    <!-- Header (always visible) -->
    <button
      type="button"
      class="w-full px-4 py-3 flex items-center justify-between gap-3 hover:bg-blue-100/50 dark:hover:bg-blue-900/20 transition-colors"
      @click="isExpanded = !isExpanded"
    >
      <div class="flex items-center gap-3">
        <div
          class="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center"
        >
          <svg
            viewBox="0 0 24 24"
            class="w-5 h-5 fill-blue-600 dark:fill-blue-400"
          >
            <path :d="mdiInformationOutline" />
          </svg>
        </div>

        <div class="text-left">
          <p class="text-sm font-medium text-blue-900 dark:text-blue-100">
            {{ $t('components.permissionMatrixInfo.title') }}
          </p>

          <p class="text-xs text-blue-600 dark:text-blue-400">
            {{ $t('components.permissionMatrixInfo.subtitle') }}
          </p>
        </div>
      </div>

      <svg
        viewBox="0 0 24 24"
        class="w-5 h-5 fill-blue-500 dark:fill-blue-400 transition-transform duration-200"
        :class="{ 'rotate-180': isExpanded }"
      >
        <path :d="mdiChevronDown" />
      </svg>
    </button>

    <!-- Expandable content -->
    <transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="max-h-0 opacity-0"
      enter-to-class="max-h-[600px] opacity-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="max-h-[600px] opacity-100"
      leave-to-class="max-h-0 opacity-0"
    >
      <div v-if="isExpanded" class="overflow-hidden">
        <div
          class="px-4 pb-4 border-t border-blue-200/50 dark:border-blue-800/50"
        >
          <!-- Permission levels -->
          <div class="mt-4">
            <h4
              class="text-xs font-semibold uppercase tracking-wide text-blue-800 dark:text-blue-300 mb-3"
            >
              {{ $t('components.permissionMatrixInfo.levelsTitle') }}
            </h4>

            <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              <div
                v-for="level in permissionLevels"
                :key="level.name"
                class="flex items-start gap-3 p-3 rounded-lg bg-white/60 dark:bg-gray-900/40 border border-blue-100 dark:border-blue-900/30"
              >
                <div
                  class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                  :class="{
                    'bg-amber-100 dark:bg-amber-900/40':
                      level.color === 'amber',
                    'bg-blue-100 dark:bg-blue-900/40': level.color === 'blue',
                    'bg-emerald-100 dark:bg-emerald-900/40':
                      level.color === 'emerald',
                    'bg-violet-100 dark:bg-violet-900/40':
                      level.color === 'violet',
                  }"
                >
                  <svg
                    viewBox="0 0 24 24"
                    class="w-4 h-4"
                    :class="{
                      'fill-amber-600 dark:fill-amber-400':
                        level.color === 'amber',
                      'fill-blue-600 dark:fill-blue-400':
                        level.color === 'blue',
                      'fill-emerald-600 dark:fill-emerald-400':
                        level.color === 'emerald',
                      'fill-violet-600 dark:fill-violet-400':
                        level.color === 'violet',
                    }"
                  >
                    <path :d="level.icon" />
                  </svg>
                </div>

                <div class="min-w-0">
                  <p
                    class="text-sm font-medium text-gray-900 dark:text-gray-100"
                  >
                    {{ level.name }}
                  </p>

                  <p class="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                    {{ level.description }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Behaviors -->
          <div class="mt-4">
            <h4
              class="text-xs font-semibold uppercase tracking-wide text-blue-800 dark:text-blue-300 mb-3"
            >
              {{ $t('components.permissionMatrixInfo.notesTitle') }}
            </h4>

            <div class="grid gap-2 sm:grid-cols-2">
              <div
                v-for="behavior in behaviors"
                :key="behavior.title"
                class="flex items-start gap-3 p-3 rounded-lg bg-white/60 dark:bg-gray-900/40 border border-blue-100 dark:border-blue-900/30"
              >
                <div
                  class="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center"
                >
                  <svg
                    viewBox="0 0 24 24"
                    class="w-4 h-4 fill-blue-600 dark:fill-blue-400"
                  >
                    <path :d="behavior.icon" />
                  </svg>
                </div>

                <div class="min-w-0">
                  <p
                    class="text-sm font-medium text-gray-900 dark:text-gray-100"
                  >
                    {{ behavior.title }}
                  </p>

                  <p class="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                    {{ behavior.text }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
