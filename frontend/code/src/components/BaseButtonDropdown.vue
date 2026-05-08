<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import BaseButton from '@/components/BaseButton.vue'
import BaseDropdownItem from '@/components/BaseDropdownItem.vue'

const props = defineProps({
  label: {
    type: String,
    default: null,
  },
  icon: {
    type: String,
    default: null,
  },
  iconSize: {
    type: [String, Number],
    default: null,
  },
  type: {
    type: String,
    default: null,
  },
  small: {
    type: Boolean,
    default: false,
  },
  color: {
    type: String,
    default: 'white',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  roundedFull: Boolean,
  dropdownItems: {
    type: Array,
    default: () => [],
  },
  align: {
    type: String,
    default: 'end', // 'start' | 'end'
  },
  dropUp: Boolean,
})

const isOpen = ref(false)
const rootEl = ref(null)
const triggerEl = ref(null)
const menuEl = ref(null)

const open = async () => {
  if (props.disabled) return
  isOpen.value = true
  await nextTick()
  const first = menuEl.value?.querySelector('[role="menuitem"]:not([disabled])')
  first?.focus()
}

const close = () => {
  if (!isOpen.value) return
  isOpen.value = false

  const el = rootEl.value?.querySelector('[data-trigger]')

  const maybeEl = el ?? triggerEl.value?.$el ?? triggerEl.value
  if (maybeEl?.focus) maybeEl.focus()
}

const toggle = () => {
  isOpen.value ? close() : open()
}

const onKeydownTrigger = (e) => {
  if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    open()
  }
}

const onKeydownMenu = (e) => {
  if (e.key === 'Escape') {
    e.preventDefault()
    close()
  }
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault()
    const items = Array.from(
      menuEl.value?.querySelectorAll('[role="menuitem"]:not([disabled])') || [],
    )
    const idx = items.findIndex((el) => el === document.activeElement)
    const nextIdx =
      e.key === 'ArrowDown'
        ? (idx + 1) % items.length
        : (idx - 1 + items.length) % items.length
    items[nextIdx]?.focus()
  }
}

const handleClickOutside = (event) => {
  if (!rootEl.value) return
  if (!rootEl.value.contains(event.target)) close()
}

const handleItemClick = () => close()

const hasNextNonDivider = (currentIndex) => {
  return filteredItems.value.slice(currentIndex + 1).some((i) => !i.divider)
}

const filteredItems = computed(() => {
  const items = props.dropdownItems
  const result = []

  for (let i = 0; i < items.length; i++) {
    const current = items[i]
    const prev = result[result.length - 1]

    if (current.divider && result.length === 0) continue

    if (current.divider && prev?.divider) continue

    result.push(current)
  }

  if (result.length > 0 && result[result.length - 1].divider) {
    result.pop()
  }

  return result
})

onMounted(() =>
  document.addEventListener('click', handleClickOutside, { capture: true }),
)
onBeforeUnmount(() =>
  document.removeEventListener('click', handleClickOutside, { capture: true }),
)
</script>

<template>
  <div ref="rootEl" class="relative inline-block">
    <BaseButton
      ref="triggerEl"
      data-trigger
      :label="label"
      :icon="icon"
      :icon-size="iconSize"
      :type="type"
      :color="color"
      :disabled="disabled"
      :rounded-full="roundedFull"
      :small="small"
      aria-haspopup="menu"
      :aria-expanded="isOpen ? 'true' : 'false'"
      @click.stop="toggle"
      @keydown="onKeydownTrigger"
    />

    <transition
      enter-active-class="transition ease-out duration-150"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        ref="menuEl"
        class="absolute min-w-44 rounded-xl border border-slate-200 bg-white shadow-xl z-50 dark:bg-slate-800 dark:border-slate-700 p-1"
        :class="[
          align === 'end' ? 'right-0' : 'left-0',
          dropUp ? 'bottom-full mb-2' : 'mt-2',
        ]"
        role="menu"
        tabindex="-1"
        @keydown.stop="onKeydownMenu"
        @click.stop
      >
        <template
          v-for="(item, index) in filteredItems"
          :key="item.id ?? index"
        >
          <div
            v-if="item.divider && hasNextNonDivider(index)"
            class="my-1 h-px bg-slate-200 dark:bg-slate-700"
          ></div>

          <BaseDropdownItem
            v-else-if="!item.divider"
            :item="item"
            :disabled="item.disabled"
            @select="handleItemClick"
          />
        </template>
      </div>
    </transition>
  </div>
</template>
