<script setup>
import {
  mdiCashMinus,
  mdiCashPlus,
  mdiCreditCardOutline,
  mdiReceipt,
} from '@mdi/js'
import { computed } from 'vue'

import BaseLevel from '@/components/BaseLevel.vue'
import CardBox from '@/components/CardBox.vue'
import IconRounded from '@/components/IconRounded.vue'
import PillTag from '@/components/PillTag.vue'

const props = defineProps({
  amount: {
    type: String,
    required: true,
  },
  date: {
    type: String,
    required: true,
  },
  business: {
    type: String,
    required: true,
  },
  status: {
    type: String,
    required: true,
  },
  name: {
    type: String,
    required: true,
  },
  account: {
    type: String,
    required: true,
  },
})

const icon = computed(() => {
  if (props.status === 'offline') {
    return {
      icon: mdiCashMinus,
      type: 'danger',
    }
  } else if (props.status === 'online') {
    return {
      icon: mdiCashPlus,
      type: 'success',
    }
  } else if (props.status === 'unknown') {
    return {
      icon: mdiReceipt,
      type: 'warning',
    }
  }

  return {
    icon: mdiCreditCardOutline,
    type: 'info',
  }
})
</script>

<template>
  <CardBox class="mb-6 last:mb-0" is-hoverable>
    <BaseLevel>
      <BaseLevel type="justify-start">
        <IconRounded :icon="icon.icon" :color="icon.type" class="md:mr-6" />

        <div class="text-center space-y-1 md:text-left md:mr-6">
          <h4 class="text-xl">{{ amount }}</h4>

          <p class="text-gray-500 dark:text-slate-400">
            <b>{{ date }}</b> via {{ business }}
          </p>
        </div>
      </BaseLevel>

      <div class="text-center md:text-right space-y-2">
        <p class="text-sm text-gray-500">
          {{ name }}
        </p>

        <div>
          <PillTag :color="icon.type" :label="status" small />
        </div>
      </div>
    </BaseLevel>
  </CardBox>
</template>
