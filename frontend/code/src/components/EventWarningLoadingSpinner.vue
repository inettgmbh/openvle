<script setup>
// Loading spinner component for event warning modals
</script>

<template>
  <div class="flex flex-col justify-center items-center min-h-[300px]">
    <svg
      class="animate-spin h-10 w-10 text-warning"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        class="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="4"
      />

      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>

    <p class="mt-4 text-warning font-medium">Daten werden geladen...</p>
  </div>
</template>
