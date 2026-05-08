<script setup>
defineOptions({ name: 'BaseTab' })

defineProps({
  id: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    default: '',
  },
  titleSlot: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})
</script>

<template>
  <div class="tab-panel" role="tabPanel">
    <br />

    <div class="tab-content">
      <slot></slot>
    </div>
  </div>
</template>

<style lang="scss">
.tab-panel {
  .tab-content {
    padding: 0.5rem;
  }
}
</style>
