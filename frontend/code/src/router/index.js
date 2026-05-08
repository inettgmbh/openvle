import { createRouter, createWebHashHistory } from 'vue-router'

import backend from '@/services'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    meta: {
      titleKey: 'objectTypes.dashboard.singular',
      noAuth: true,
    },
    beforeEnter: backend.auth.requireAuth,
    component: () => import('@/views/dashboard/DashboardGeneric.vue'),
  },
  {
    path: '/activities',
    meta: {
      type: 'activities',
    },
    children: [
      {
        path: '',
        name: 'activitiesList',
        meta: {
          titleKey: 'objectTypes.activity.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/activity/ActivityList.vue'),
      },
      {
        path: ':id',
        name: 'activitiesDetail',
        meta: {
          titleKey: 'objectTypes.activity.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/activity/ActivityDetail.vue'),
      },
    ],
  },
  {
    path: '/applications',
    meta: {
      type: 'applications',
    },
    children: [
      {
        path: '',
        name: 'applicationsList',
        meta: {
          titleKey: 'objectTypes.application.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/application/ApplicationList.vue'),
      },
      {
        path: ':id',
        name: 'applicationsDetail',
        meta: {
          titleKey: 'objectTypes.application.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/application/ApplicationDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'applicationsEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.application.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/application/ApplicationEdit.vue'),
      },
      {
        path: 'create',
        name: 'applicationsCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.application.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/application/ApplicationCreate.vue'),
      },
    ],
  },
  {
    path: '/apps',
    redirect: () => `/applications`,
  },
  {
    path: '/apps/:id',
    redirect: (to) => {
      const { params } = to
      return `/applications/${params.id}`
    },
  },
  {
    path: '/auth',
    meta: {
      noAuth: true,
    },
    children: [
      {
        path: 'login',
        name: 'login',
        meta: {
          titleKey: 'routes.login',
        },
        beforeEnter: backend.auth.requireLogout,
        component: () => import('@/views/auth/AuthLogin.vue'),
        params: true,
      },
      {
        path: 'oidc/callback',
        name: 'oidcCallback',
        meta: {
          titleKey: 'routes.oidcCallback',
        },
        beforeEnter: backend.auth.loginOIDC,
        component: { template: '<div>Signing in…</div>' },
        params: true,
      },
    ],
  },
  {
    path: '/courses',
    meta: {
      type: 'courses',
    },
    children: [
      {
        path: '',
        name: 'coursesList',
        meta: {
          titleKey: 'objectTypes.course.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/course/CourseList.vue'),
      },
      {
        path: ':id',
        name: 'coursesDetail',
        meta: {
          titleKey: 'objectTypes.course.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/course/CourseDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'coursesEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.course.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/course/CourseEdit.vue'),
      },
      {
        path: 'create',
        name: 'coursesCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.course.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/course/CourseCreate.vue'),
      },
    ],
  },
  {
    path: '/events',
    meta: {
      type: 'events',
    },
    children: [
      {
        path: '',
        name: 'eventsList',
        meta: {
          titleKey: 'objectTypes.event.plural',
          noAuth: true,
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/event/EventList.vue'),
      },
      {
        path: ':id',
        name: 'eventsDetail',
        meta: {
          titleKey: 'objectTypes.event.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/event/EventDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'eventsEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.event.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/event/EventEdit.vue'),
      },
      {
        path: 'create',
        name: 'eventsCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.event.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/event/EventCreate.vue'),
      },
    ],
  },
  {
    path: '/mails',
    meta: {
      type: 'mails',
    },
    children: [
      {
        path: '',
        name: 'mailsList',
        meta: {
          titleKey: 'objectTypes.mail.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/mail/MailList.vue'),
      },
      {
        path: ':id',
        name: 'mailsDetail',
        meta: {
          titleKey: 'objectTypes.mail.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/mail/MailDetail.vue'),
      },
      {
        path: 'create',
        name: 'mailsCreate',
        meta: {
          titleKey: 'common.sendTitle',
          titleEntityKey: 'objectTypes.mail.singular',
          permission: 'send',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/mail/MailCreate.vue'),
      },
    ],
  },
  {
    path: '/mail-actions',
    meta: {
      type: 'mail_templates', // yes, because they use the same permissions
    },
    children: [
      {
        path: '',
        name: 'mailActionsList',
        meta: {
          titleKey: 'objectTypes.mailAction.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/mailaction/MailActionList.vue'),
      },
      {
        path: ':id',
        name: 'mailActionsDetail',
        meta: {
          titleKey: 'objectTypes.mailAction.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/mailaction/MailActionDetail.vue'),
      },
    ],
  },
  {
    path: '/mailtemplates',
    redirect: () => `/mail-templates`,
  },
  {
    path: '/mailtemplates/:id',
    redirect: (to) => {
      const { params } = to
      return `/mail-templates/${params.id}`
    },
  },
  {
    path: '/mail-templates',
    meta: {
      type: 'mail_templates',
    },
    children: [
      {
        path: '',
        name: 'mailTemplatesList',
        meta: {
          titleKey: 'objectTypes.mailTemplate.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/mailtemplate/MailTemplateList.vue'),
      },
      {
        path: ':id',
        name: 'mailTemplatesDetail',
        meta: {
          titleKey: 'objectTypes.mailTemplate.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/mailtemplate/MailTemplateDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'mailTemplatesEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.mailTemplate.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/mailtemplate/MailTemplateEdit.vue'),
      },
      {
        path: 'create',
        name: 'mailTemplatesCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.mailTemplate.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/mailtemplate/MailTemplateCreate.vue'),
      },
    ],
  },
  {
    path: '/mails_templates',
    redirect: () => `/mail-templates`,
  },
  {
    path: '/mails_templates/:id',
    redirect: (to) => {
      const { params } = to
      return `/mail-templates/${params.id}`
    },
  },
  {
    path: '/guacamoles',
    meta: {
      type: 'guacamoles',
    },
    children: [
      {
        path: '',
        name: 'guacamolesList',
        meta: {
          titleKey: 'objectTypes.guacamole.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/guacamole/GuacamoleList.vue'),
      },
      {
        path: ':id',
        name: 'guacamolesDetail',
        meta: {
          titleKey: 'objectTypes.guacamole.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/guacamole/GuacamoleDetail.vue'),
      },
      {
        path: 'create',
        name: 'guacamolesCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.guacamole.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/guacamole/GuacamoleCreate.vue'),
      },
    ],
  },
  {
    path: '/connections',
    meta: {
      type: 'guacamole_connection_profiles',
    },
    children: [
      {
        path: '',
        name: 'connectionsList',
        meta: {
          titleKey: 'objectTypes.guacamoleConnectionProfile.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/connection/ConnectionList.vue'),
      },
      {
        path: ':id',
        name: 'connectionsDetail',
        meta: {
          titleKey: 'objectTypes.guacamoleConnectionProfile.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/connection/ConnectionDetail.vue'),
      },
      {
        path: 'clone',
        name: 'connectionsClone',
        meta: {
          titleKey: 'common.cloneTitle',
          titleEntityKey: 'objectTypes.guacamoleConnectionProfile.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/connection/ConnectionClone.vue'),
      },
      {
        path: 'create',
        name: 'connectionsCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.guacamoleConnectionProfile.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/connection/ConnectionCreate.vue'),
      },
    ],
  },
  {
    path: '/guacamole_connection_profiles',
    redirect: () => `/connections`,
  },
  {
    path: '/guacamole_connection_profiles/:id',
    redirect: (to) => {
      const { params } = to
      return `/connections/${params.id}`
    },
  },
  {
    path: '/os',

    meta: {
      type: 'os',
    },
    children: [
      {
        path: '',
        name: 'osList',
        meta: {
          titleKey: 'objectTypes.os.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/os/OSList.vue'),
      },
      {
        path: ':id',
        name: 'osDetail',
        meta: {
          titleKey: 'objectTypes.os.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/os/OSDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'osEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.os.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/os/OSEdit.vue'),
      },
      {
        path: 'create',
        name: 'osCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.os.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/os/OSCreate.vue'),
      },
    ],
  },
  {
    path: '/policies',
    meta: {
      type: 'policies',
    },
    children: [
      {
        path: '',
        name: 'policiesList',
        meta: {
          titleKey: 'objectTypes.policy.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/policy/PolicyList.vue'),
      },
      {
        path: ':id',
        name: 'policiesDetail',
        meta: {
          titleKey: 'objectTypes.policy.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/policy/PolicyDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'policiesEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.policy.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/policy/PolicyEdit.vue'),
      },
      {
        path: 'create',
        name: 'policiesCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.policy.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/policy/PolicyCreate.vue'),
      },
    ],
  },
  {
    path: '/policy/:id',
    name: 'policy',
    meta: {
      titleKey: 'common.confirmTitle',
      titleEntityKey: 'objectTypes.policy.singular',
      noAuth: true,
    },
    beforeEnter: backend.auth.requirePolicyAgree,
    component: () => import('@/views/policy/PolicyAgree.vue'),
  },
  {
    path: '/roles',
    meta: {
      type: 'roles',
    },
    children: [
      {
        path: '',
        name: 'rolesList',
        meta: {
          titleKey: 'objectTypes.role.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/role/RoleList.vue'),
      },
      {
        path: ':id',
        name: 'rolesDetail',
        meta: {
          titleKey: 'objectTypes.role.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/role/RoleDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'rolesEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.role.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/role/RoleEdit.vue'),
      },
      {
        path: 'create',
        name: 'rolesCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.role.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/role/RoleCreate.vue'),
      },
    ],
  },
  {
    path: '/scim/clients',
    meta: {
      type: 'scim_clients',
      requiredSetting: 'features.scim.enabled',
    },
    children: [
      {
        path: '',
        name: 'scimClientsList',
        meta: {
          titleKey: 'objectTypes.scimClient.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/scimclient/ScimClientList.vue'),
      },
      {
        path: ':id',
        name: 'scimClientsDetail',
        meta: {
          titleKey: 'objectTypes.scimClient.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/scimclient/ScimClientDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'scimClientsEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.scimClient.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/scimclient/ScimClientEdit.vue'),
      },
      {
        path: 'create',
        name: 'scimClientsCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.scimClient.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/scimclient/ScimClientCreate.vue'),
      },
    ],
  },
  {
    path: '/scim/providers',
    meta: {
      type: 'scim_providers',
      requiredSetting: 'features.scim.enabled',
    },
    children: [
      {
        path: '',
        name: 'scimProvidersList',
        meta: {
          titleKey: 'objectTypes.scimProvider.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/scimprovider/ScimProviderList.vue'),
      },
      {
        path: ':id',
        name: 'scimProvidersDetail',
        meta: {
          titleKey: 'objectTypes.scimProvider.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/scimprovider/ScimProviderDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'scimProvidersEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.scimProvider.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/scimprovider/ScimProviderEdit.vue'),
      },
      {
        path: 'create',
        name: 'scimProvidersCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.scimProvider.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/scimprovider/ScimProviderCreate.vue'),
      },
    ],
  },
  {
    path: '/proxmox',
    meta: {
      type: 'proxmox',
    },
    children: [
      {
        path: 'nodes',
        children: [
          {
            path: '',
            name: 'proxmoxNodeList',
            meta: {
              titleKey: 'routes.proxmoxNodeList',
              permission: 'read',
            },
            beforeEnter: backend.auth.requireAuth,
            component: () => import('@/views/proxmox/ProxmoxNodeList.vue'),
          },
          {
            path: ':id',
            name: 'proxmoxNodeDetail',
            meta: {
              titleKey: 'routes.proxmoxNodeDetail',
              permission: 'read',
            },
            beforeEnter: backend.auth.requireAuth,
            component: () => import('@/views/proxmox/ProxmoxNodeDetail.vue'),
          },
        ],
      },
      {
        path: 'stats',
        name: 'proxmoxStats',
        meta: {
          titleKey: 'routes.proxmoxStats',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/proxmox/ProxmoxNodesStats.vue'),
      },
    ],
  },
  {
    path: '/settings',
    meta: {
      type: 'system',
    },
    children: [
      {
        path: '',
        name: 'settingsList',
        meta: {
          titleKey: 'routes.settingsList',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/system/SystemSettingList.vue'),
      },
    ],
  },
  {
    path: '/tags',
    meta: {
      type: 'tags',
      noAuth: true,
    },
    children: [
      {
        path: '',
        name: 'tagsList',
        meta: {
          titleKey: 'objectTypes.tag.plural',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/tag/TagList.vue'),
      },
      {
        path: ':key',
        name: 'tagsByKey',
        meta: {
          titleKey: 'routes.tagsByKey',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/tag/TagList.vue'),
      },
      {
        path: ':key/:value',
        name: 'tagsByKeyValue',
        meta: {
          titleKey: 'routes.tagsByKeyValue',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/tag/TagList.vue'),
      },
    ],
  },
  {
    path: '/tasks',
    meta: {
      type: 'tasks',
    },
    children: [
      {
        path: '',
        name: 'tasksList',
        meta: {
          titleKey: 'objectTypes.task.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/task/TaskList.vue'),
      },
      {
        path: ':id',
        name: 'tasksDetail',
        meta: {
          titleKey: 'objectTypes.task.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/task/TaskDetail.vue'),
      },
      {
        path: 'subtasks',
        meta: {
          type: 'sub_tasks',
        },
        children: [
          {
            path: ':id',
            name: 'subtasksDetail',
            meta: {
              titleKey: 'routes.subtasksDetail',
              permission: 'read',
            },
            beforeEnter: backend.auth.requireAuth,
            component: () => import('@/views/task/SubTaskDetail.vue'),
          },
        ],
      },
    ],
  },
  {
    path: '/templates',
    meta: {
      type: 'templates',
    },
    children: [
      {
        path: '',
        name: 'templatesList',
        meta: {
          titleKey: 'objectTypes.template.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/template/TemplateList.vue'),
      },
      {
        path: ':id',
        name: 'templatesDetail',
        meta: {
          titleKey: 'objectTypes.template.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/template/TemplateDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'templatesEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.template.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/template/TemplateEdit.vue'),
      },
      {
        path: 'create',
        name: 'templatesCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.template.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/template/TemplateCreate.vue'),
      },
      {
        path: 'import',
        name: 'templatesImport',
        meta: {
          titleKey: 'common.importTitle',
          titleEntityKey: 'objectTypes.template.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/template/TemplateImport.vue'),
      },
    ],
  },
  {
    path: '/users',
    meta: {
      type: 'users',
    },
    children: [
      {
        path: '',
        name: 'usersList',
        meta: {
          titleKey: 'objectTypes.user.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/user/UserList.vue'),
      },
      {
        path: ':id',
        name: 'usersDetail',
        meta: {
          titleKey: 'objectTypes.user.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/user/UserDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'usersEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.user.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/user/UserEdit.vue'),
      },
      {
        path: 'create',
        name: 'usersCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.user.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/user/UserCreate.vue'),
      },
      {
        path: 'import',
        name: 'usersImport',
        meta: {
          titleKey: 'common.importTitle',
          titleEntityKey: 'objectTypes.user.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/user/UserImport.vue'),
      },
    ],
  },
  {
    path: '/vendors',
    meta: {
      type: 'vendors',
    },
    children: [
      {
        path: '',
        name: 'vendorsList',
        meta: {
          titleKey: 'objectTypes.vendor.plural',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/vendor/VendorList.vue'),
      },
      {
        path: ':id',
        name: 'vendorsDetail',
        meta: {
          titleKey: 'objectTypes.vendor.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/vendor/VendorDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'vendorsEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.vendor.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/vendor/VendorEdit.vue'),
      },
      {
        path: 'create',
        name: 'vendorsCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.vendor.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/vendor/VendorCreate.vue'),
      },
    ],
  },
  {
    path: '/vendor',
    redirect: () => `/vendors`,
  },
  {
    path: '/vendor/:id',
    redirect: (to) => {
      const { params } = to
      return `/vendors/${params.id}`
    },
  },
  {
    path: '/vms',
    meta: {
      type: 'vms',
    },
    children: [
      {
        path: '',
        name: 'vmsList',
        meta: {
          titleKey: 'objectTypes.virtualMachine.plural',
          noAuth: true,
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/vm/VMList.vue'),
      },
      {
        path: ':id',
        name: 'vmsDetail',
        meta: {
          titleKey: 'objectTypes.virtualMachine.singular',
          permission: 'read',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/vm/VMDetail.vue'),
      },
      {
        path: ':id/edit',
        name: 'vmsEdit',
        meta: {
          titleKey: 'common.editTitle',
          titleEntityKey: 'objectTypes.virtualMachine.singular',
          permission: 'update',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/vm/VMEdit.vue'),
      },
      {
        path: 'create',
        name: 'vmsCreate',
        meta: {
          titleKey: 'common.createTitle',
          titleEntityKey: 'objectTypes.virtualMachine.singular',
          permission: 'create',
        },
        beforeEnter: backend.auth.requireAuth,
        component: () => import('@/views/vm/VMCreate.vue'),
      },
    ],
  },
  {
    path: '/vm',
    redirect: () => `/vms`,
  },
  {
    path: '/vm/:id',
    redirect: (to) => {
      const { params } = to
      return `/vms/${params.id}`
    },
  },
  {
    path: '/virtual_machines',
    redirect: () => `/vms`,
  },
  {
    path: '/virtual_machines/:id',
    redirect: (to) => {
      const { params } = to
      return `/vms/${params.id}`
    },
  },
  {
    meta: {
      titleKey: 'routes.profile',
      noAuth: true,
    },
    path: '/profile',
    name: 'profile',
    beforeEnter: backend.auth.requireAuth,
    component: () => import('@/views/generic/UserProfile.vue'),
  },
  {
    path: '/:catchAll(.*)',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0 }
  },
})

export default router
