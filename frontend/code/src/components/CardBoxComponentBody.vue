<script setup>
defineProps({
  noPadding: Boolean,
  isModal: Boolean,
  hasSearch: Boolean,
})
</script>

<template>
  <div
    class="flex-1"
    :class="{
      'p-6': !noPadding,
      'min-h-0 overflow-y-auto': isModal && !hasSearch,
    }"
  >
    <slot />
  </div>
</template>
