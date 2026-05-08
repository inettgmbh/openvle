<script setup>
import {
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from 'chart.js'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Title,
)

const props = defineProps({
  rrdData: {
    type: Array,
    required: true,
  },
  metrics: {
    type: Array,
    default: () => ['cpu'],
  },
  title: {
    type: String,
    required: true,
  },
  animation: {
    type: Boolean,
    default: false,
  },
  timeframe: {
    type: String,
    default: 'hour',
  },
})

const { t } = useI18n()
const canvas = ref(null)
let chartInstance = null

const metricTransform = {
  cpu: (d) => d.cpu * 100,
  mem: (d) => (d.memused && d.memtotal ? (d.memused / d.memtotal) * 100 : 0),
  netin: (d) => d.netin / 1024 / 1024, // MB/s
  netout: (d) => d.netout / 1024 / 1024, // MB/s
  iowait: (d) => d.iowait * 1000, // ms
  arcsize: (d) => d.arcsize / 1024 / 1024 / 1024, // GB
  memhost: (d) => d.memhost / 1024 / 1024 / 1024, // GB
  loadavg: (d) => d.loadavg,
  memused: (d) => d.memused / 1024 / 1024 / 1024, // GB
  memavailable: (d) => d.memavailable / 1024 / 1024 / 1024, // GB
  pressurecpusome: (d) => d.pressurecpusome * 100,
  pressurememorysome: (d) => d.pressurememorysome * 100,
  pressurememoryfull: (d) => d.pressurememoryfull * 100,
  pressureiosome: (d) => d.pressureiosome * 100,
  pressureiofull: (d) => d.pressureiofull * 100,
  swapused: (d) => d.swapused / 1024 / 1024 / 1024, // GB
  swaptotal: (d) => d.swaptotal / 1024 / 1024 / 1024, // GB
  rootused: (d) => d.rootused / 1024 / 1024 / 1024, // GB
  roottotal: (d) => d.roottotal / 1024 / 1024 / 1024, // GB
  maxcpu: (d) => d.maxcpu,
}

const metricLabelKeys = [
  'cpu',
  'mem',
  'memused',
  'memavailable',
  'memhost',
  'swapused',
  'swaptotal',
  'rootused',
  'roottotal',
  'netin',
  'netout',
  'arcsize',
  'iowait',
  'loadavg',
  'pressurecpusome',
  'pressurememorysome',
  'pressurememoryfull',
  'pressureiosome',
  'pressureiofull',
  'maxcpu',
]

const metricLabels = computed(() =>
  Object.fromEntries(
    metricLabelKeys.map((key) => [key, t(`components.proxmoxRrdChart.${key}`)]),
  ),
)

const metricColors = {
  cpu: 'rgba(75, 192, 192, 1)',
  mem: 'rgba(255, 99, 132, 1)',
  memused: 'rgba(255, 159, 64, 1)',
  memavailable: 'rgba(153, 102, 255, 1)',
  memhost: 'rgba(13, 192, 25, 1)',
  swapused: 'rgba(201, 203, 207, 1)',
  swaptotal: 'rgba(201, 203, 207, 0.5)',
  rootused: 'rgba(100, 149, 237, 1)',
  roottotal: 'rgba(70, 130, 180, 0.5)',
  netin: 'rgba(54, 162, 235, 1)',
  netout: 'rgba(255, 206, 86, 1)',
  arcsize: 'rgba(106, 90, 205, 1)',
  iowait: 'rgba(0, 191, 255, 1)',
  loadavg: 'rgba(128, 0, 128, 1)',
  pressurecpusome: 'rgba(255, 0, 0, 1)',
  pressurememorysome: 'rgba(255, 140, 0, 1)',
  pressurememoryfull: 'rgba(255, 69, 0, 1)',
  pressureiosome: 'rgba(0, 128, 0, 1)',
  pressureiofull: 'rgba(46, 139, 87, 1)',
  maxcpu: 'rgba(169, 169, 169, 1)',
}

function formatLabel(timestamp) {
  const date = new Date(timestamp * 1000)
  switch (props.timeframe) {
    case 'hour':
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    case 'day':
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    case 'week':
      return date.toLocaleDateString([], {
        weekday: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    case 'month':
      return date.toLocaleDateString([], {
        day: '2-digit',
        month: '2-digit',
      })
    case 'year':
      return date.toLocaleDateString([], {
        month: 'short',
        year: '2-digit',
      })
    case 'decade':
      return date.toLocaleDateString([], {
        month: 'short',
        year: 'numeric',
      })
    default:
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
  }
}

const chartData = computed(() => {
  const labels = props.rrdData.map((d) => formatLabel(d.time))

  const datasets = props.metrics.map((metric) => {
    const transform = metricTransform[metric] || ((d) => d[metric] ?? 0)
    const data = props.rrdData.map(transform)

    return {
      label: metricLabels.value[metric] || metric,
      data,
      borderColor: metricColors[metric] || 'gray',
      fill: false,
      tension: 0.3,
      pointRadius: 0,
    }
  })

  return { labels, datasets }
})

function renderChart() {
  if (chartInstance) {
    chartInstance.destroy()
  }

  chartInstance = new Chart(canvas.value, {
    type: 'line',
    data: chartData.value,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: props.animation,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: t('components.proxmoxRrdChart.timeLabel'),
          },
          ticks: {
            maxTicksLimit: 10,
          },
        },
        y: {
          beginAtZero: true,
          display: true,
          title: {
            display: true,
          },
        },
      },
      plugins: {
        legend: { display: true },
        tooltip: { enabled: true },
        title: {
          display: true,
          text: props.title,
          font: {
            size: 16,
          },
          padding: {
            top: 10,
            bottom: 10,
          },
        },
      },
    },
  })
}

onMounted(() => {
  renderChart()
})

watch(chartData, () => {
  renderChart()
})
</script>

<template>
  <div class="w-full h-64">
    <canvas ref="canvas" class="w-full h-full" />
  </div>
</template>
