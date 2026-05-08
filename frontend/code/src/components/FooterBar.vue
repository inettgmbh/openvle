<script setup>
import { computed } from 'vue'

import BaseLevel from '@/components/BaseLevel.vue'
import { containerMaxW } from '@/config.js'
import { useMainStore } from '@/stores/main'
import { useStyleStore } from '@/stores/style.js'

const mainStore = useMainStore()

const year = new Date().getFullYear()
const customerName = computed(
  () => mainStore.settings?.branding?.customer?.name,
)
const customerURL01 = computed(
  () => mainStore.settings?.branding?.customer?.url01,
)
const customerURL02 = computed(
  () => mainStore.settings?.branding?.customer?.url02,
)
const versionFrontend = process.env.VUE_APP_VERSION
const versionBackend = computed(
  () => mainStore.settings?.version?.backend?.label,
)
</script>

<template>
  <footer class="py-2 px-6" :class="containerMaxW">
    <BaseLevel>
      <div class="text-center md:text-left">
        <b
          >&copy; {{ year }},
          <a :href="customerURL01" target="_blank">{{ customerName }}</a></b
        >

        <slot />
      </div>

      <div class="text-center">
        <small
          >Frontend: "{{ versionFrontend }}" - Backend: "{{
            versionBackend
          }}"</small
        >
      </div>

      <div class="md:py-2">
        <a :href="customerURL02">
          <img
            :src="
              useStyleStore().darkMode
                ? '/logo-with-text-dark.svg'
                : '/logo-with-text-light.svg'
            "
            alt="Footer Logo"
            class="w-auto h-8 md:h-6"
          />
        </a>
      </div>
    </BaseLevel>
  </footer>
</template>
