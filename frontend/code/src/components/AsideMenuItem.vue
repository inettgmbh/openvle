<script setup>
import { mdiMinus, mdiPlus } from '@mdi/js'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getButtonColor } from '@/colors.js'
import AsideMenuList from '@/components/AsideMenuList.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import { useStyleStore } from '@/stores/style.js'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  isDropdownList: Boolean,
})

const route = useRoute()

const router = useRouter()

const emit = defineEmits(['menu-click'])

const styleStore = useStyleStore()

const hasColor = computed(() => props.item && props.item.color)

const asideMenuItemActiveStyle = computed(() =>
  hasColor.value ? '' : styleStore.asideMenuItemActiveStyle,
)

const resolvedHref = computed(() => {
  if (props.item.to) {
    return router.resolve(props.item.to).href
  }
  return props.item.href ?? null
})

const isDropdownActive = ref(false)

const componentClass = computed(() => [
  props.isDropdownList ? 'py-3 px-6 text-sm' : 'py-3',
  hasColor.value
    ? getButtonColor(props.item.color, false, true)
    : `${styleStore.asideMenuItemStyle} dark:text-slate-300 dark:hover:text-white`,
])

const hasDropdown = computed(() => !!props.item.menu)

const menuClick = (event) => {
  emit('menu-click', event, props.item)

  if (hasDropdown.value) {
    isDropdownActive.value = !isDropdownActive.value
  }
}

const handleClick = (event) => {
  /** When modifier-clicking (right-click, Cmd, Ctrl) → maintain default behavior */
  if (
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey ||
    event.button !== 0
  ) {
    return
  }

  /** Route links → use router.push so URL and view change together */
  if (props.item.to) {
    event.preventDefault()
    router.push(props.item.to)
    return
  }

  /** External links → allow default <a> behavior */
  if (props.item.href) {
    return
  }

  /** Otherwise, open/trigger dropdown */
  menuClick(event)
}

const handleMiddleClick = (event) => {
  // event.button === 1 is the middle mouse button. Most browsers handle the
  // <a href>'s default "open in new tab" natively, but we add explicit
  // handling here because some setups (extensions, custom event handling)
  // suppress the native fallback.
  if (event.button !== 1) return
  if (!resolvedHref.value) return
  event.preventDefault()
  window.open(resolvedHref.value, '_blank')
}

const isActiveRoute = (routePath) => {
  if (!routePath) return false

  // Special case for root route '/'
  if (routePath === '/' && route.path !== '/') {
    return false
  }

  return route.path.startsWith(routePath)
}

// Ensure dropdown stays open if navigating to a child route
if (hasDropdown.value) {
  props.item.menu.forEach((element) => {
    if (route.path.startsWith(element.to)) {
      isDropdownActive.value = true
    }
  })
}
</script>

<template>
  <li>
    <component
      :is="'a'"
      :href="resolvedHref"
      :target="item.target ?? null"
      class="flex cursor-pointer"
      :class="componentClass"
      @click="(e) => handleClick(e)"
      @auxclick="(e) => handleMiddleClick(e)"
    >
      <BaseIcon
        v-if="item.icon"
        :path="item.icon"
        class="flex-none"
        :class="[isActiveRoute(item.to) ? asideMenuItemActiveStyle : '']"
        w="w-16"
        :size="18"
      />

      <span
        class="grow text-ellipsis line-clamp-1"
        :class="[
          { 'pr-1': !hasDropdown },
          isActiveRoute(item.to) ? asideMenuItemActiveStyle : '',
        ]"
        >{{ item.labelKey ? $t(item.labelKey) : item.label }}</span
      >

      <BaseIcon
        v-if="hasDropdown"
        :path="isDropdownActive ? mdiMinus : mdiPlus"
        class="flex-none"
        :class="[isActiveRoute(item.to) ? asideMenuItemActiveStyle : '']"
        w="w-12"
      />
    </component>

    <AsideMenuList
      v-if="hasDropdown"
      :menu="item.menu"
      :class="[
        styleStore.asideMenuDropdownStyle,
        isDropdownActive ? 'block dark:bg-slate-800/50' : 'hidden',
      ]"
      is-dropdown-list
    />
  </li>
</template>
