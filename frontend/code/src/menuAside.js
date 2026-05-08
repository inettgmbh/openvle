import {
  mdiAccountBoxOutline,
  mdiAccountMultipleOutline,
  mdiApplicationBrackets,
  mdiApps,
  mdiCalendarClock,
  mdiChartBar,
  mdiCloudKeyOutline,
  mdiCloudLockOutline,
  mdiCloudOutline,
  mdiCloudSyncOutline,
  mdiCog,
  mdiCogBox,
  mdiDomain,
  mdiEmail,
  mdiEmailFast,
  mdiEmailMultiple,
  mdiEmailSync,
  mdiFileSign,
  mdiFileTree,
  mdiImport,
  mdiMonitor,
  mdiRemoteDesktop,
  mdiSchoolOutline,
  mdiServer,
  mdiTag,
  mdiTextBoxOutline,
  mdiVectorArrangeAbove,
  mdiViewDashboardOutline,
} from '@mdi/js'

const menuItems = [
  {
    to: '/',
    icon: mdiViewDashboardOutline,
    labelKey: 'objectTypes.dashboard.singular',
    permission: null,
  },
  {
    labelKey: 'objectTypes.mail.plural',
    icon: mdiEmail,
    menu: [
      {
        to: '/mails',
        labelKey: 'nav.emailsSent',
        icon: mdiEmailFast,
        model: 'mails',
      },
      {
        to: '/mail-templates',
        labelKey: 'nav.emailTemplates',
        icon: mdiEmailMultiple,
        model: 'mail_templates',
      },
      {
        to: '/mail-actions',
        labelKey: 'nav.emailActions',
        icon: mdiEmailSync,
        model: 'mail_templates',
      },
    ],
  },
  {
    labelKey: 'nav.infrastructure',
    icon: mdiImport,
    menu: [
      {
        to: '/applications',
        labelKey: 'objectTypes.application.plural',
        icon: mdiApps,
        model: 'applications',
      },
      {
        to: '/os',
        labelKey: 'objectTypes.os.plural',
        icon: mdiApplicationBrackets,
        model: 'os',
      },
      {
        to: '/vendors',
        labelKey: 'objectTypes.vendor.plural',
        icon: mdiDomain,
        model: 'vendors',
      },
    ],
  },
  {
    labelKey: 'nav.proxmox',
    icon: mdiCloudOutline,
    menu: [
      {
        to: '/proxmox/nodes',
        labelKey: 'nav.proxmoxNodes',
        icon: mdiServer,
        model: 'proxmox',
      },
      {
        to: '/proxmox/stats',
        labelKey: 'nav.proxmoxStats',
        icon: mdiChartBar,
        model: 'proxmox',
      },
    ],
  },
  {
    labelKey: 'nav.system',
    icon: mdiCogBox,
    menu: [
      {
        to: '/activities',
        labelKey: 'objectTypes.activity.plural',
        icon: mdiTextBoxOutline,
        model: 'activities',
      },
      {
        to: '/settings',
        labelKey: 'nav.settings',
        icon: mdiCog,
        model: 'system',
      },
      {
        to: '/tasks',
        labelKey: 'objectTypes.task.plural',
        icon: mdiFileTree,
        model: 'tasks',
      },
    ],
  },
  {
    to: '/tags',
    labelKey: 'objectTypes.tag.plural',
    icon: mdiTag,
    model: 'tags',
    permission: null,
  },
  {
    to: '/courses',
    labelKey: 'objectTypes.course.plural',
    icon: mdiSchoolOutline,
    model: 'courses',
  },
  {
    to: '/events',
    labelKey: 'objectTypes.event.plural',
    icon: mdiCalendarClock,
    permission: null,
    model: 'events',
  },
  {
    labelKey: 'objectTypes.guacamole.plural',
    icon: mdiRemoteDesktop,
    menu: [
      {
        to: '/guacamoles',
        labelKey: 'objectTypes.guacamole.plural',
        icon: mdiRemoteDesktop,
        model: 'guacamoles',
      },
      {
        to: '/connections',
        labelKey: 'nav.connectionTemplates',
        icon: mdiRemoteDesktop,
        model: 'guacamole_connection_profiles',
      },
    ],
  },
  {
    to: '/vms',
    labelKey: 'objectTypes.virtualMachine.plural',
    icon: mdiMonitor,
    permission: null,
    model: 'vms',
  },
  {
    to: '/templates',
    labelKey: 'nav.vmTemplates',
    icon: mdiVectorArrangeAbove,
    model: 'templates',
  },
  {
    labelKey: 'nav.accessControl',
    icon: mdiCloudKeyOutline,
    menu: [
      {
        to: '/users',
        labelKey: 'objectTypes.user.plural',
        icon: mdiAccountBoxOutline,
        model: 'users',
      },
      {
        to: '/policies',
        labelKey: 'objectTypes.policy.plural',
        icon: mdiFileSign,
        model: 'policies',
      },
      {
        to: '/roles',
        labelKey: 'objectTypes.role.plural',
        icon: mdiAccountMultipleOutline,
        model: 'roles',
      },
      {
        to: '/scim/clients',
        labelKey: 'objectTypes.scimClient.plural',
        icon: mdiCloudSyncOutline,
        model: 'scim_clients',
        requiredSetting: 'features.scim.enabled',
      },
      {
        to: '/scim/providers',
        labelKey: 'objectTypes.scimProvider.plural',
        icon: mdiCloudLockOutline,
        model: 'scim_providers',
        requiredSetting: 'features.scim.enabled',
      },
    ],
  },
]

const resolvePath = (obj, path) =>
  path.split('.').reduce((acc, key) => acc?.[key], obj)

const filterMenu = async (items, mainStore) => {
  const filteredItems = []

  for (const item of items) {
    // Skip if required setting is not enabled
    if (
      item.requiredSetting &&
      !resolvePath(mainStore.settings, item.requiredSetting)
    ) {
      continue
    }

    if (
      item.permission === null ||
      (item.to &&
        item.model &&
        (await mainStore.userCan(item.model, 'read', '/')))
    ) {
      let newItem = { ...item }

      if (item.menu && Array.isArray(item.menu)) {
        newItem.menu = await filterMenu(item.menu, mainStore)
        if (newItem.menu.length === 0) {
          delete newItem.menu
        }
      }

      filteredItems.push(newItem)
    } else if (item.menu && Array.isArray(item.menu)) {
      let subMenu = await filterMenu(item.menu, mainStore)
      if (subMenu.length > 0) {
        let newItem = { ...item, menu: subMenu }
        filteredItems.push(newItem)
      }
    }
  }

  return filteredItems
}

export const getFilteredMenu = async (mainStore) => {
  return await filterMenu(menuItems, mainStore)
}
