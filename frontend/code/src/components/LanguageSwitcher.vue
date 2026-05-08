<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButtonDropdown from '@/components/BaseButtonDropdown.vue'
import { switchLocale } from '@/composables/useLocale'
import { SUPPORTED_LOCALES } from '@/i18n'
import { getLocaleLabel } from '@/utils/localeData'

const props = defineProps({
  dropUp: {
    type: Boolean,
    default: true,
  },
})

const { locale, t } = useI18n()

const dropdownItems = computed(() =>
  SUPPORTED_LOCALES.map((code) => ({
    id: code,
    label: getLocaleLabel(code),
    disabled: locale.value === code,
    onClick: () => switchLocale(code),
  })),
)

const triggerLabel = computed(() => getLocaleLabel(locale.value))
</script>

<template>
  <BaseButtonDropdown
    :label="triggerLabel"
    :drop-up="dropUp"
    align="end"
    color="white"
    :dropdown-items="dropdownItems"
    :aria-label="t('navbar.language')"
  />
</template>
