import {
  mdiConsole,
  mdiDesktopClassic,
  mdiKubernetes,
  mdiMonitor,
  mdiNetwork,
} from '@mdi/js'
import { computed } from 'vue'

import { protocolConnectionFilter } from '@/utils/dataUtils'

/**
 * Protocol configuration with icons and default ports.
 */
export const protocolConfig = {
  k8s: {
    icon: mdiKubernetes,
    label: 'K8S',
    description: 'Kubernetes',
    port: 8080,
  },
  rdp: {
    icon: mdiDesktopClassic,
    label: 'RDP',
    description: 'Remote Desktop',
    port: 3389,
  },
  ssh: {
    icon: mdiConsole,
    label: 'SSH',
    description: 'Secure Shell',
    port: 22,
  },
  vnc: {
    icon: mdiMonitor,
    label: 'VNC',
    description: 'Virtual Network',
    port: 5901,
  },
  tel: {
    icon: mdiNetwork,
    label: 'Telnet',
    description: 'Telnet',
    port: 23,
  },
}

/**
 * Composable for connection form logic.
 *
 * @param {Object} options - Configuration options.
 * @param {import('vue').Ref<Set>} [options.existingProtocols] - Set of already used protocols.
 * @returns {Object} Protocol buttons and helper functions.
 */
export function useConnectionForm(options = {}) {
  const { existingProtocols = null } = options

  const protocolOptions = computed(() => protocolConnectionFilter())

  const protocolButtons = computed(() => {
    const opts = protocolOptions.value || []
    const used = existingProtocols?.value || new Set()

    return opts.map((opt) => {
      const value = typeof opt === 'string' ? opt : opt?.value
      const config = protocolConfig[value] || {}
      const disabled = used.has(value)

      return {
        value,
        label: config.label || value?.toUpperCase(),
        description: config.description || '',
        icon: config.icon || mdiNetwork,
        port: config.port,
        disabled,
      }
    })
  })

  /**
   * Get the default port for a protocol.
   *
   * @param {string} protocol - Protocol key.
   * @returns {number|null} Default port or null.
   */
  function getDefaultPort(protocol) {
    return protocolConfig[protocol]?.port ?? null
  }

  return {
    protocolConfig,
    protocolOptions,
    protocolButtons,
    getDefaultPort,
  }
}
