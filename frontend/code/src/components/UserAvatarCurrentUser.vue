<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { useMainStore } from '@/stores/main'

const mainStore = useMainStore()
</script>

<template>
  <UserAvatar :userid="mainStore.user.id ? mainStore.user.id : 'example'">
    <slot />
  </UserAvatar>
</template>
