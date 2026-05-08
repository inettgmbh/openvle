<script setup>
import { RouterView } from 'vue-router'

import RateLimitModal from '@/components/RateLimitModal.vue'
</script>

<template>
  <RouterView />

  <RateLimitModal />
</template>
