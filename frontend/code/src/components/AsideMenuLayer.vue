<script setup>
import { mdiClose } from '@mdi/js'
import { computed } from 'vue'

import AsideMenuList from '@/components/AsideMenuList.vue'
import BaseDivider from '@/components/BaseDivider.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import { useMaintenancePolling } from '@/composables/useMaintenancePolling'
import { useMainStore } from '@/stores/main'
import { useStyleStore } from '@/stores/style.js'

defineProps({
  menu: {
    type: Array,
    required: true,
  },
})

const mainStore = useMainStore()
const { bannerHeight } = useMaintenancePolling()

const emit = defineEmits(['menu-click', 'aside-lg-close-click'])

const styleStore = useStyleStore()

const menuClick = (event, item) => {
  emit('menu-click', event, item)
}

const asideLgCloseClick = (event) => {
  emit('aside-lg-close-click', event)
}

const applicationLabel = computed(() => mainStore.settings?.branding?.app?.name)

const asideTop = computed(() => `${bannerHeight.value}px`)
const asideHeight = computed(() => `calc(100vh - ${bannerHeight.value}px)`)
</script>

<template>
  <aside
    id="aside"
    :style="{ top: asideTop, height: asideHeight }"
    class="lg:py-2 lg:pl-2 w-60 fixed flex z-40 transition-position overflow-hidden"
  >
    <div
      :class="styleStore.asideStyle"
      class="lg:rounded-2xl flex-1 flex flex-col overflow-hidden dark:bg-slate-900 bg-gray-100"
    >
      <div
        :class="styleStore.asideBrandStyle"
        class="flex flex-row h-18 items-center justify-between dark:bg-slate-900 bg-gray-100"
      >
        <div class="text-center flex-1 lg:pl-6 xl:pl-0">
          <router-link to="/" class="block">
            <img
              :src="
                useStyleStore().darkMode
                  ? '/logo-with-text-dark.svg'
                  : '/logo-with-text-light.svg'
              "
              alt="Portal Logo"
              class="w-auto h-7 md:h-8 mx-auto my-3"
            />
          </router-link>

          <BaseDivider :nav-bar="true" class="xl:ml-6 xl:mr-6" />

          <b>{{ applicationLabel }}</b>

          <BaseDivider :nav-bar="true" class="xl:ml-6 xl:mr-6" />
        </div>

        <button
          class="hidden lg:inline-block xl:hidden p-3"
          @click.prevent="asideLgCloseClick"
        >
          <BaseIcon :path="mdiClose" />
        </button>
      </div>

      <div
        :class="
          styleStore.darkMode
            ? 'aside-scrollbars-[slate]'
            : styleStore.asideScrollbarsStyle
        "
        class="flex-1 overflow-y-auto overflow-x-hidden"
      >
        <AsideMenuList :menu="menu" @menu-click="menuClick" />
      </div>
    </div>
  </aside>
</template>
