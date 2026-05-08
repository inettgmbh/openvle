<script setup>
import {
  nextTick,
  onBeforeUnmount,
  onBeforeUpdate,
  onMounted,
  ref,
  useSlots,
  watch,
} from 'vue'
import { useRoute, useRouter } from 'vue-router'

defineOptions({ name: 'BaseTabs' })

const props = defineProps({
  defaultIndex: { type: Number, default: 0 },
  resetTabs: { type: Boolean, default: false },
  direction: {
    type: String,
    default: 'horizontal',
    validator: (value) => ['horizontal', 'vertical'].includes(value),
  },
  position: {
    type: String,
    default: 'left',
    validator: (value) => ['left', 'start', 'end', 'center'].includes(value),
  },
  reverse: { type: Boolean, default: false },
})

const emit = defineEmits(['tabChanged'])
const slots = useSlots()

const route = useRoute()
const router = useRouter()

const selectedIndex = ref(0)
const tabs = ref([])
const _tabItems = ref([])

const onTabKeyDown = (e) => {
  if (e.ctrlKey || e.metaKey) {
    if (parseInt(e.key) - 1 in tabs.value) {
      e.preventDefault()
      switchTab(e, parseInt(e.key) - 1, tabs.value[parseInt(e.key) - 1])
    }
  }
}

const reset = () => {
  selectedIndex.value = 0
}

const switchTab = (_, index, isDisabled) => {
  if (!isDisabled) {
    selectedIndex.value = index
    emit('tabChanged', _tabItems.value[index]?.props?.id || index)
  }
}

onMounted(async () => {
  getTabItems()
  await nextTick()

  const activeTabId = route.query.tab
  const foundIndex = _tabItems.value.findIndex(
    (tabVNode) => tabVNode.props && tabVNode.props.id === activeTabId,
  )

  if (foundIndex !== -1) {
    selectedIndex.value = foundIndex
    emit('tabChanged', _tabItems.value[foundIndex]?.props?.id || foundIndex)
  } else {
    selectedIndex.value = props.defaultIndex
    emit('tabChanged', _tabItems.value[props.defaultIndex]?.props?.id || 0)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onTabKeyDown)
})

watch(
  () => props.defaultIndex,
  (newValue) => {
    if (newValue !== selectedIndex.value) {
      selectedIndex.value = newValue
    }
  },
)

watch(
  () => props.resetTabs,
  (newValue) => {
    if (newValue === true) reset()
  },
)

watch(selectedIndex, (newVal) => {
  const activeTabVNode = _tabItems.value[newVal]
  if (!activeTabVNode) return
  const activeTabId = activeTabVNode.props?.id

  router.replace({
    query: {
      ...route.query,
      tab: activeTabId,
    },
  })

  setTimeout(() => {
    const tabElements = document.querySelectorAll('.tab-list__item')
    const activeTabElement = tabElements[newVal]
    if (activeTabElement) {
      activeTabElement.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'center',
      })
    }
  }, 50)
})

onBeforeUpdate(() => {
  getTabItems()
})

const getTabItems = () => {
  _tabItems.value.splice(0, _tabItems.value.length)
  const children = slots.default?.() || []

  const extractTabs = (nodes) => {
    nodes.forEach((node) => {
      if (!node || typeof node !== 'object') return

      if (node.type?.name === 'BaseTab') {
        _tabItems.value.push(node)
      } else if (Array.isArray(node.children)) {
        extractTabs(node.children)
      }
    })
  }

  extractTabs(children)
}

const getTitleSlotContent = (titleSlot) => {
  let slotContent = null
  let shouldSkip = false
  slots.default().forEach((item) => {
    if (shouldSkip) return

    if (item.type === 'template' && item.props.name === titleSlot) {
      slotContent = item.children
      shouldSkip = true
    } else if (item.children && item.children.length) {
      item.children.forEach((cItem) => {
        if (shouldSkip) return
        if (cItem.props && cItem.props.name === titleSlot) {
          slotContent = cItem.children
          shouldSkip = true
        }
      })
    }
  })
  return slotContent === null ? [] : slotContent
}

defineExpose({
  reset,
})
</script>

<template>
  <div
    :class="`tabs ${props.direction} ${props.reverse ? 'reverse' : ''}`"
    role="tabs"
  >
    <ul
      :class="`tab-list ${props.position} flex overflow-x-auto overflow-y-hidden whitespace-nowrap border-b border-gray-300 w-full max-w-full px-2 sm:px-4`"
      role="tabList"
    >
      <li
        v-for="(tab, index) in _tabItems"
        :key="index"
        class="tab-list__item"
        tabindex="0"
        role="tabItem"
        :aria-selected="selectedIndex === index ? 'true' : 'false'"
        :aria-disabled="
          tab.props?.disabled === true || tab.props?.disabled === ''
            ? 'true'
            : 'false'
        "
        @click="
          switchTab(
            $event,
            index,
            tab.props?.disabled === true || tab.props?.disabled === '',
          )
        "
      >
        <template v-if="tab.props?.['title-slot']">
          <component :is="getTitleSlotContent(tab.props['title-slot'])" />
        </template>

        <template v-else>
          {{ tab.props?.title }}
        </template>
      </li>
    </ul>

    <transition name="fade" mode="out-in">
      <keep-alive>
        <component
          :is="_tabItems[selectedIndex]"
          :key="_tabItems[selectedIndex]?.props?.id || selectedIndex"
          class="tab"
        />
      </keep-alive>
    </transition>
  </div>
</template>

<style lang="scss">
:root {
  --primary-color: #4313aa;
  --border-color: #e2e2e2;
  --disabled-text-color: #999;
}
.tabs {
  display: grid;
  grid-template-columns: 1fr;
  .tab-list {
    list-style: none;
    display: flex;
    padding-left: 0;
    border-bottom: 1px solid var(--border-color);
    &.center {
      justify-content: center;
    }
    &.end {
      justify-content: flex-end;
    }
    &__item {
      padding: 8px 10px;
      cursor: pointer;
      user-select: none;
      transition: border 0.3s ease-in-out;
      position: relative;
      bottom: -1px;
      text-transform: uppercase;
      font-size: 0.85rem;
      letter-spacing: 0.05rem;

      &:not(:first-child) {
        margin-left: 10px;
      }

      &[aria-selected='true'] {
        border-bottom: 2px solid var(--primary-color);
        font-weight: 1000;
      }
      &[aria-disabled='true'] {
        cursor: not-allowed;
        color: var(--disabled-text-color);
      }
    }
  }

  &.horizontal {
    &.reverse {
      .tab-list {
        grid-row: 2;
        border: none;
        border-top: 1px solid var(--border-color);
      }
    }
  }

  &.vertical {
    grid-template-columns: auto 1fr;
    gap: 1rem;
    .tab-list {
      flex-direction: column;
      border-bottom: none;
      border-right: 1px solid var(--border-color);

      &__item {
        margin-left: 0;
        border-radius: 0;

        &[aria-selected='true'] {
          border: none;
          border-left: 2px solid var(--primary-color);
        }
      }
    }

    &.reverse {
      grid-template-columns: 1fr auto;
      .tab-list {
        grid-column: 2;
        border: none;
        border-left: 1px solid var(--border-color);
      }

      .tab {
        grid-row: 1;
        grid-column: 1;
      }
    }
  }
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
