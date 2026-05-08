<script setup>
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import highlight from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { config, MdEditor, MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import mermaid from 'mermaid'
import * as prettier from 'prettier'
import parserMarkdown from 'prettier/plugins/markdown'
import screenfull from 'screenfull'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { useStyleStore } from '@/stores/style'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  action: {
    type: String,
    default: 'edit', // 'edit' or 'view'
    validator: (val) => ['edit', 'view'].includes(val),
  },
  toolbarsExclude: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue', 'scrolled'])

config({
  markdownItConfig(mdit) {
    mdit.set({ linkify: false })
  },
  editorExtensions: {
    cropper: {
      instance: Cropper,
    },
    highlight: {
      instance: highlight,
    },
    katex: {
      instance: katex,
    },
    mermaid: {
      instance: mermaid,
    },
    prettier: {
      prettierInstance: prettier,
      parserMarkdownInstance: parserMarkdown,
    },
    screenfull: {
      instance: screenfull,
    },
  },
})

const componentType = computed(() =>
  props.action === 'view' ? MdPreview : MdEditor,
)

const componentProps = computed(() => {
  if (props.action === 'view') {
    return {
      modelValue: props.modelValue,
      'no-img-zoom-in': true,
      'no-katex': true,
      'no-mermaid': true,
      theme: useStyleStore().darkMode ? 'dark' : 'light',
      language: 'en-US',
    }
  }

  return {
    modelValue: props.modelValue,
    'onUpdate:modelValue': (val) => emit('update:modelValue', val),
    language: 'en-US',
    'html-preview': false,
    'no-mermaid': true,
    'no-img-zoom-in': true,
    'no-katex': true,
    'no-upload-img': true,
    'page-fullscreen': false,
    preview: true,
    'scroll-auto': true,
    'show-toolbar-name': false,
    theme: useStyleStore().darkMode ? 'dark' : 'light',
    'toolbars-exclude': [
      'image',
      'mermaid',
      'katex',
      'save',
      'prettier',
      'fullscreen',
      'htmlPreview',
      'catalog',
      'github',
      ...props.toolbarsExclude,
    ],
  }
})

const wrapperClass = computed(() => {
  return props.action === 'view'
    ? 'border border-gray-500 rounded-md p-4 max-h-96'
    : ''
})

const wrapperRef = ref(null)

const wrapperStyle = computed(() =>
  props.action === 'view'
    ? {
        overflowY: 'scroll',
        backgroundColor: useStyleStore().darkMode ? '#1e293b' : '#ffffff',
        color: useStyleStore().darkMode ? '#ffffff' : '#000000',
      }
    : {},
)

const onScroll = () => {
  if (props.action !== 'view') return
  checkScrollState()
}
const hasEmittedScrolled = ref(false)

const checkScrollState = () => {
  if (hasEmittedScrolled.value) return

  const el = wrapperRef.value
  if (!el) return

  const isScrolledToBottom =
    el.scrollTop + el.clientHeight >= el.scrollHeight - 1
  const isNotScrollable = el.scrollHeight <= el.clientHeight

  if ((isNotScrollable || isScrolledToBottom) && props.modelValue !== '') {
    emit('scrolled')
    hasEmittedScrolled.value = true
  }
}

let observer = null

onMounted(() => {
  if (props.action !== 'view') return

  const el = wrapperRef.value
  if (!el) return

  observer = new MutationObserver(() => {
    checkScrollState()
  })

  observer.observe(el, {
    childList: true,
    subtree: true,
  })
})

onBeforeUnmount(() => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
})

watch(
  () => props.modelValue,
  () => {
    hasEmittedScrolled.value = false
  },
)
</script>

<template>
  <div
    ref="wrapperRef"
    :class="wrapperClass"
    :style="wrapperStyle"
    @scroll="onScroll"
  >
    <component :is="componentType" v-bind="componentProps" />
  </div>
</template>

<style scoped>
.md-editor-dark {
  --md-bk-color: #1e293b;
  --md-color: #fefefe;
}
</style>
