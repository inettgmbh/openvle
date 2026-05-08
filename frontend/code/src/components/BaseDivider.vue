<script setup>
const props = defineProps({
  navBar: Boolean,
})
</script>

<template>
  <hr
    :class="
      props.navBar
        ? 'hidden lg:block lg:my-0.5 dark:border-white'
        : 'my-6 -mx-6 dark:border-white'
    "
    class="border-t border-black"
  />
</template>
