<script>
import { createAvatar } from '@dicebear/core'

import { avatarStyleValidator } from '@/utils/dataUtils' // eslint-disable-line import/order

// Module-level cache — shared across all instances, survives remounts
const avatarCache = new Map()

async function resolveAvatar(userid, avatarType) {
  const validType = avatarStyleValidator(avatarType) ? avatarType : 'glass'
  const cacheKey = `${userid}:${validType}`

  if (avatarCache.has(cacheKey)) {
    return avatarCache.get(cacheKey)
  }

  const { [validType]: style } = await import('@dicebear/collection')
  const svg = createAvatar(style, { seed: userid }).toString()
  const src = `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
  avatarCache.set(cacheKey, src)
  return src
}
</script>

<script setup>
import { ref, watchEffect } from 'vue'

import { useMainStore } from '@/stores/main'

const props = defineProps({
  userid: {
    type: String,
    required: true,
  },
  alt: {
    type: String,
    default: 'User Avatar',
  },
  avatar: {
    type: String,
    default: null,
  },
})

const mainStore = useMainStore()

const avatarSrc = ref(
  avatarCache.get(
    `${props.userid}:${avatarStyleValidator(mainStore?.settings?.avatars?.type) ? mainStore.settings.avatars.type : 'glass'}`,
  ) ?? '',
)

watchEffect(async () => {
  if (props.avatar) {
    avatarSrc.value = props.avatar
    return
  }

  avatarSrc.value = await resolveAvatar(
    props.userid,
    mainStore?.settings?.avatars?.type,
  )
})
</script>

<template>
  <div>
    <img
      :src="avatarSrc"
      class="rounded-full block h-auto w-full max-w-full bg-gray-100 dark:bg-slate-800"
    />

    <slot />
  </div>
</template>
