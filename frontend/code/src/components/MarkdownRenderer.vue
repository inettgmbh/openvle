<template>
  <div v-if="compiledMarkdown" :innerHTML="compiledMarkdown"></div>
</template>

<script setup>
import { marked } from 'marked'
import { ref, watch } from 'vue'

const props = defineProps({
  markdownText: {
    type: String,
    required: false,
    default: null,
  },
})

const compiledMarkdown = ref('')

watch(
  () => props.markdownText,
  (newVal) => {
    if (newVal) {
      compiledMarkdown.value = marked(newVal)
    }
  },
  { immediate: true },
)
</script>
