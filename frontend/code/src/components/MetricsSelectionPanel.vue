<script setup>
import { mdiUpdate } from '@mdi/js'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Multiselect from 'vue-multiselect'
import 'vue-multiselect/dist/vue-multiselect.css'

import BaseButton from '@/components/BaseButton.vue'
import CardBox from '@/components/CardBox.vue'
import FormField from '@/components/FormField.vue'

const props = defineProps({
  hosts: {
    type: Array,
    required: false,
    default: () => [],
  },
  type: {
    type: String,
    required: true,
    validator: (val) => ['node', 'vm'].includes(val),
  },
})

const { t } = useI18n()
const counterUpdates = ref(0)

const emit = defineEmits(['submit'])

const selectedServer = ref(
  Array.isArray(props.hosts) && props.hosts.length === 1
    ? [props.hosts[0]]
    : [],
)

const selectedTimeframe = ref(null)
const selectedCf = ref(null)
const selectedMetrics = ref([])

const showServerSelect = computed(() => props.hosts.length !== 1)

const optionsTimeframe = computed(() => {
  const base = [
    { value: 'hour', label: t('components.metricsSelectionPanel.lastHour') },
    { value: 'day', label: t('components.metricsSelectionPanel.lastDay') },
    { value: 'week', label: t('components.metricsSelectionPanel.lastWeek') },
    {
      value: 'month',
      label: t('components.metricsSelectionPanel.lastMonth'),
    },
    { value: 'year', label: t('components.metricsSelectionPanel.lastYear') },
  ]
  if (props.type === 'node') {
    base.push({
      value: 'decade',
      label: t('components.metricsSelectionPanel.lastDecade'),
    })
  }
  return base
})

const optionsCf = computed(() => [
  {
    value: 'AVERAGE',
    label: t('components.metricsSelectionPanel.average'),
  },
  { value: 'MAX', label: t('components.metricsSelectionPanel.max') },
])

// Set initial selections after computed options are available
selectedTimeframe.value = optionsTimeframe.value[0]
selectedCf.value = optionsCf.value[0]

const metricOptions = computed(() => {
  const commonMetrics = [
    {
      value: 'cpu',
      label: t('components.metricsSelectionPanel.cpuUsage'),
    },
    {
      value: 'netin',
      label: t('components.metricsSelectionPanel.networkIn'),
    },
    {
      value: 'netout',
      label: t('components.metricsSelectionPanel.networkOut'),
    },
  ]

  const pressureMetrics = [
    {
      value: 'pressurememorysome',
      label: t('components.metricsSelectionPanel.ramPressure'),
    },
    {
      value: 'pressurememoryfull',
      label: t('components.metricsSelectionPanel.ramPressureFull'),
    },
    {
      value: 'pressureiosome',
      label: t('components.metricsSelectionPanel.ioPressure'),
    },
    {
      value: 'pressureiofull',
      label: t('components.metricsSelectionPanel.ioPressureFull'),
    },
  ]

  const nodeOnly = [
    {
      value: 'iowait',
      label: t('components.metricsSelectionPanel.ioWait'),
    },
    {
      value: 'loadavg',
      label: t('components.metricsSelectionPanel.loadAverage'),
    },
    {
      value: 'pressurecpusome',
      label: t('components.metricsSelectionPanel.cpuPressure'),
    },
    {
      value: 'mem',
      label: t('components.metricsSelectionPanel.ramUsageNode'),
    },
    {
      value: 'arcsize',
      label: t('components.metricsSelectionPanel.arcSize'),
    },
    {
      value: 'swapused',
      label: t('components.metricsSelectionPanel.swapUsed'),
    },
    {
      value: 'swaptotal',
      label: t('components.metricsSelectionPanel.swapTotal'),
    },
    {
      value: 'rootused',
      label: t('components.metricsSelectionPanel.storageUsed'),
    },
    {
      value: 'roottotal',
      label: t('components.metricsSelectionPanel.storageTotal'),
    },
    {
      value: 'maxcpu',
      label: t('components.metricsSelectionPanel.cpuTotal'),
    },
    {
      value: 'memused',
      label: t('components.metricsSelectionPanel.ramUsed'),
    },
    {
      value: 'memavailable',
      label: t('components.metricsSelectionPanel.ramAvailable'),
    },
  ]

  const vmOnly = [
    {
      value: 'memhost',
      label: t('components.metricsSelectionPanel.ramUsageHost'),
    },
  ]

  return [
    ...commonMetrics,
    ...(props.type === 'node' ? nodeOnly : []),
    ...(props.type === 'vm' ? vmOnly : []),
    ...pressureMetrics,
  ].sort((a, b) => a.label.localeCompare(b.label))
})

function submit() {
  counterUpdates.value = counterUpdates.value + 1
  emit('submit', {
    hosts: selectedServer.value,
    metrics: selectedMetrics.value,
    timeframe: selectedTimeframe.value.value,
    cf: selectedCf.value.value,
  })
}
</script>

<template>
  <CardBox class="mb-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <FormField
        v-if="showServerSelect"
        :label="$t('components.metricsSelectionPanel.server')"
      >
        <Multiselect
          id="selectedServer"
          v-model="selectedServer"
          :options="hosts"
          :multiple="true"
          :close-on-select="false"
          :clear-on-select="false"
          :preserve-search="true"
          :max="8"
          :select-label="$t('components.metricsSelectionPanel.enterToSelect')"
          :selected-label="$t('components.metricsSelectionPanel.selected')"
          :deselect-label="$t('components.metricsSelectionPanel.enterToRemove')"
          label="label"
          track-by="value"
          :placeholder="$t('components.metricsSelectionPanel.selectServer')"
          class="w-full"
        >
          <template #maxElements>
            <span>{{
              $t('components.metricsSelectionPanel.maxElements')
            }}</span>
          </template>
        </Multiselect>
      </FormField>

      <FormField :label="$t('components.metricsSelectionPanel.metrics')">
        <Multiselect
          id="selectedMetrics"
          v-model="selectedMetrics"
          :options="metricOptions"
          :multiple="true"
          :close-on-select="false"
          :clear-on-select="false"
          :preserve-search="true"
          :max="8"
          :select-label="$t('components.metricsSelectionPanel.enterToSelect')"
          :selected-label="$t('components.metricsSelectionPanel.selected')"
          :deselect-label="$t('components.metricsSelectionPanel.enterToRemove')"
          label="label"
          track-by="value"
          :placeholder="$t('components.metricsSelectionPanel.selectMetrics')"
          class="w-full"
        >
          <template #maxElements>
            <span>{{
              $t('components.metricsSelectionPanel.maxElements')
            }}</span>
          </template>
        </Multiselect>
      </FormField>

      <FormField :label="$t('components.metricsSelectionPanel.timeframe')">
        <Multiselect
          id="selectedTimeframe"
          v-model="selectedTimeframe"
          :options="optionsTimeframe"
          :select-label="$t('components.metricsSelectionPanel.enterToSelect')"
          :selected-label="$t('components.metricsSelectionPanel.selected')"
          :deselect-label="$t('components.metricsSelectionPanel.enterToRemove')"
          label="label"
          track-by="value"
          :placeholder="$t('components.metricsSelectionPanel.selectTimeframe')"
          class="w-full"
        />
      </FormField>

      <FormField
        :label="$t('components.metricsSelectionPanel.cfConsolidation')"
      >
        <Multiselect
          id="selectedCf"
          v-model="selectedCf"
          :options="optionsCf"
          :select-label="$t('components.metricsSelectionPanel.enterToSelect')"
          :selected-label="$t('components.metricsSelectionPanel.selected')"
          :deselect-label="$t('components.metricsSelectionPanel.enterToRemove')"
          label="label"
          track-by="value"
          :placeholder="$t('components.metricsSelectionPanel.selectCf')"
          class="w-full"
        />
      </FormField>
    </div>

    <div class="mt-4 text-right">
      <BaseButton
        :icon="mdiUpdate"
        :label="
          counterUpdates == 0
            ? $t('components.metricsSelectionPanel.createChart')
            : $t('components.metricsSelectionPanel.updateChart')
        "
        color="info"
        @click="submit"
      />
    </div>
  </CardBox>
</template>

<style>
.multiselect {
  @apply rounded border border-none shadow-sm;
}

.multiselect .multiselect__tags {
  @apply dark:bg-gray-800 dark:border-gray-700 dark:text-white;
}

.multiselect__tags .multiselect__single {
  @apply dark:bg-gray-800;
}

.multiselect .multiselect__input {
  @apply dark:bg-gray-800;
}

.multiselect .multiselect__content-wrapper {
  @apply dark:bg-gray-800 dark:text-white dark:border-gray-800;
}

.multiselect .multiselect__option--selected {
  @apply dark:bg-gray-700 dark:text-white;
}
</style>
