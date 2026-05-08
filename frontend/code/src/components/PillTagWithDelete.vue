<script setup>
import { mdiCheck, mdiClose } from '@mdi/js'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { colorsBgLight, colorsOutline } from '@/colors.js'
import BaseIcon from '@/components/BaseIcon.vue'

const { t } = useI18n()

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  color: {
    type: String,
    required: true,
  },
  icon: {
    type: String,
    default: null,
  },
  outline: Boolean,
  small: Boolean,
  handleClick: {
    type: Function,
    default: undefined,
  },
  onDelete: {
    type: Function,
    default: undefined,
  },
  disabled: Boolean,
})

const confirmDelete = ref(false)
const tagRef = ref(null)
const tagWidth = ref(null)

const classes = computed(() => [
  'inline-flex items-center justify-between rounded-full leading-none border transition-all relative flex-shrink-0',
  props.small
    ? 'py-1 px-2 text-xs min-w-[8rem] h-6'
    : 'py-1.5 px-3 text-sm min-w-[10rem] h-8',
  props.outline ? colorsOutline[props.color] : colorsBgLight[props.color],
  props.disabled ? 'cursor-not-allowed' : 'cursor-pointer',
])

const style = computed(() =>
  tagWidth.value ? { width: `${tagWidth.value}px` } : undefined,
)

function handleOutsideClick(event) {
  if (
    confirmDelete.value &&
    tagRef.value &&
    !tagRef.value.contains(event.target)
  ) {
    confirmDelete.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  nextTick(() => {
    if (tagRef.value) {
      tagWidth.value = tagRef.value.offsetWidth
    }
  })
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick)
})

watch(confirmDelete, async (newVal) => {
  if (!newVal && tagRef.value) {
    await nextTick()
    tagWidth.value = tagRef.value.offsetWidth
  }
})
</script>

<template>
  <div
    ref="tagRef"
    :class="classes"
    :style="style"
    :aria-disabled="disabled"
    @click="!disabled && !confirmDelete && handleClick && handleClick()"
  >
    <BaseIcon
      v-if="icon"
      :path="icon"
      h="h-4"
      w="w-4"
      :class="[small ? 'h-3.5 w-3.5 mr-1' : 'mr-2']"
      :size="small ? 14 : null"
    />

    <Transition name="fade-tag" mode="out-in">
      <template v-if="!confirmDelete">
        <div class="flex items-center gap-2 w-full">
          <span class="flex-grow text-center whitespace-nowrap leading-normal">
            {{ label }}
          </span>

          <button
            v-if="onDelete"
            :title="t('components.pillTagWithDelete.deleteTag')"
            class="h-5 w-5 rounded-full bg-gray-200 hover:bg-gray-300 text-gray-700 flex items-center justify-center"
            @click.stop="confirmDelete = true"
          >
            <BaseIcon :path="mdiClose" size="12" w="w-4" h="h-4" />
          </button>
        </div>
      </template>

      <template v-else>
        <div class="flex w-full items-center justify-between gap-2">
          <span class="flex-grow text-center leading-normal whitespace-nowrap">
            {{ t('components.pillTagWithDelete.sure') }}
          </span>

          <div class="flex items-center gap-1">
            <button
              class="h-5 w-5 rounded-full bg-green-200 hover:bg-green-300 text-green-800 flex items-center justify-center"
              :title="t('components.pillTagWithDelete.confirmDelete')"
              @click.stop="
                () => {
                  confirmDelete = false
                  onDelete?.()
                }
              "
            >
              <BaseIcon :path="mdiCheck" size="12" w="w-4" h="h-4" />
            </button>

            <button
              class="h-5 w-5 rounded-full bg-gray-300 hover:bg-gray-400 text-gray-800 flex items-center justify-center"
              :title="t('common.cancel')"
              @click.stop="confirmDelete = false"
            >
              <BaseIcon :path="mdiClose" size="12" w="w-4" h="h-4" />
            </button>
          </div>
        </div>
      </template>
    </Transition>
  </div>
</template>

<style scoped>
.fade-tag-enter-active,
.fade-tag-leave-active {
  transition: opacity 0.2s ease;
}
.fade-tag-enter-from,
.fade-tag-leave-to {
  opacity: 0;
}
</style>
