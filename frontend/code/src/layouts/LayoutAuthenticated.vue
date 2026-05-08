<script setup>
import { mdiBackburger, mdiForwardburger, mdiMenu } from '@mdi/js'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import AsideMenu from '@/components/AsideMenu.vue'
import BaseIcon from '@/components/BaseIcon.vue'
import FooterBar from '@/components/FooterBar.vue'
import MaintenanceBanner from '@/components/MaintenanceBanner.vue'
import NavBar from '@/components/NavBar.vue'
import NavBarItemPlain from '@/components/NavBarItemPlain.vue'
import { switchLocale, useLocale } from '@/composables/useLocale'
import { useMaintenancePolling } from '@/composables/useMaintenancePolling'
import { getFilteredMenu } from '@/menuAside.js'
import menuNavBar from '@/menuNavBar.js'
import { useMainStore } from '@/stores/main.js'
import { useStyleStore } from '@/stores/style.js'

const layoutAsidePadding = 'xl:pl-60'

const mainStore = useMainStore()
useLocale()
const { bannerHeight } = useMaintenancePolling()

const styleStore = useStyleStore()

const menuAside = ref([])

const router = useRouter()

const isAsideMobileExpanded = ref(false)
const isAsideLgActive = ref(false)

// NavBar height is 56px (h-14)
const NAV_BAR_HEIGHT = 56

const contentPaddingTop = computed(
  () => `${NAV_BAR_HEIGHT + bannerHeight.value}px`,
)
const navBarTop = computed(() => `${bannerHeight.value}px`)

router.beforeEach(() => {
  isAsideMobileExpanded.value = false
  isAsideLgActive.value = false
})

const menuClick = (event, item) => {
  if (item.isLanguageSwitch) {
    switchLocale(item.isLanguageSwitch)
  }

  if (item.isToggleLightDark) {
    styleStore.nextThemeMode()
  }

  if (item.isLogout) {
    mainStore.logout()
    router.push('/auth/login')
  }
}

onMounted(async () => {
  menuAside.value = await getFilteredMenu(mainStore)

  styleStore.initializeThemeWatcher()
})

watch(
  () => mainStore.settingsStatus,
  async (status) => {
    if (status === 'loaded') {
      menuAside.value = await getFilteredMenu(mainStore)
    }
  },
)

onUnmounted(() => {
  styleStore.destroyThemeWatcher()
})
</script>

<template>
  <div
    :class="{
      dark: styleStore.darkMode,
      'overflow-hidden lg:overflow-visible': isAsideMobileExpanded,
    }"
  >
    <MaintenanceBanner />

    <div
      :class="[layoutAsidePadding, { 'ml-60 lg:ml-0': isAsideMobileExpanded }]"
      :style="{ paddingTop: contentPaddingTop }"
      class="min-h-screen w-screen transition-position lg:w-auto bg-gray-50 dark:bg-slate-800 dark:text-slate-100"
    >
      <NavBar
        :menu="menuNavBar"
        :style="{ top: navBarTop }"
        :class="[
          layoutAsidePadding,
          { 'ml-60 lg:ml-0': isAsideMobileExpanded },
        ]"
        @menu-click="menuClick"
      >
        <NavBarItemPlain
          display="flex lg:hidden"
          @click.prevent="isAsideMobileExpanded = !isAsideMobileExpanded"
        >
          <BaseIcon
            :path="isAsideMobileExpanded ? mdiBackburger : mdiForwardburger"
            size="24"
          />
        </NavBarItemPlain>

        <NavBarItemPlain
          display="hidden lg:flex xl:hidden"
          @click.prevent="isAsideLgActive = true"
        >
          <BaseIcon :path="mdiMenu" size="24" />
        </NavBarItemPlain>

        <NavBarItemPlain use-margin>
          <!-- <FormControl
            placeholder="Search (ctrl+k)"
            ctrl-k-focus
            transparent
            borderless
          /> -->
        </NavBarItemPlain>
      </NavBar>

      <AsideMenu
        :is-aside-mobile-expanded="isAsideMobileExpanded"
        :is-aside-lg-active="isAsideLgActive"
        :menu="menuAside"
        @menu-click="menuClick"
        @aside-lg-close-click="isAsideLgActive = false"
      />

      <slot />

      <FooterBar />
    </div>
  </div>
</template>
