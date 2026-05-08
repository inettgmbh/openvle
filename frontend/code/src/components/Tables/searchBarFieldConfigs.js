import {
  mdiAccount,
  mdiCalendar,
  mdiEmailOutline,
  mdiListBoxOutline,
  mdiNetwork,
} from '@mdi/js'

import { SearchOperators } from '@/components/Tables/searchOperators'
import { getI18nT } from '@/i18n'
import {
  protectedObjectFilter,
  protocolConnectionFilter,
  roleProtectedFilter,
  statusEventFilter,
  statusTemplateFilter,
  statusUserFilter,
  statusVMFilter,
} from '@/utils/dataUtils'
import { emailStatusIcon } from '@/utils/icons'

/**
 * Search bar field configs per object type.
 * Shared between list views and detail view tabs to avoid duplication.
 * Each function accepts an optional `{ exclude }` array to filter out
 * fields by key (matches `field.key ?? field.preset`).
 */

function applyExclude(fields, exclude) {
  if (!exclude?.length) return fields
  return fields.filter((f) => !exclude.includes(f.key ?? f.preset))
}

export function roleSearchBarFields({ exclude } = {}) {
  const t = getI18nT()
  return applyExclude(
    [
      { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'key', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      {
        preset: 'protected',
        label: t('common.type'),
        operators: SearchOperators.EQUALS_ONLY_ONLY,
        options: roleProtectedFilter(),
      },
    ],
    exclude,
  )
}

export function userSearchBarFields({ exclude } = {}) {
  return applyExclude(
    [
      { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'username', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'email', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      {
        preset: 'status',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
        options: statusUserFilter(),
      },
    ],
    exclude,
  )
}

export function vmSearchBarFields({ exclude } = {}) {
  return applyExclude(
    [
      { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'description', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'cpu', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'ram', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'disk', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'os', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'ipv4', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'template', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'event', operators: SearchOperators.EQUALS_ONLY_ONLY },
      {
        preset: 'status',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
        options: statusVMFilter(),
      },
      {
        preset: 'preventDelete',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
        options: protectedObjectFilter(),
      },
      { preset: 'proxmoxId', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'proxmoxNode', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
    ],
    exclude,
  )
}

export function courseSearchBarFields({ exclude } = {}) {
  return applyExclude(
    [
      { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'description', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
    ],
    exclude,
  )
}

export function connectionSearchBarFields({ exclude } = {}) {
  const t = getI18nT()
  return applyExclude(
    [
      {
        preset: 'vm',
        key: 'objectId',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
      },
      {
        preset: 'template',
        key: 'objectId',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
      },
      { preset: 'username', operators: SearchOperators.CONTAINS_ONLY },
      {
        preset: 'protocol',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
        options: protocolConnectionFilter(),
      },
      {
        key: 'port',
        label: t('common.port'),
        icon: mdiNetwork,
        operators: SearchOperators.EQUALS_ONLY_ONLY,
      },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
    ],
    exclude,
  )
}

export function applicationSearchBarFields({ exclude } = {}) {
  return applyExclude(
    [
      { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'key', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'description', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'vendor', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
    ],
    exclude,
  )
}

export function osSearchBarFields({ exclude } = {}) {
  return applyExclude(
    [
      { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'key', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'description', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'vendor', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
    ],
    exclude,
  )
}

export function guacamoleSearchBarFields({ exclude } = {}) {
  const t = getI18nT()
  return applyExclude(
    [
      { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
      {
        preset: 'createdById',
        key: 'userId',
        label: t('common.user'),
        operators: SearchOperators.EQUALS_ONLY_ONLY,
      },
      {
        preset: 'event',
        key: 'eventId',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
      },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
    ],
    exclude,
  )
}

export function templateSearchBarFields({ exclude } = {}) {
  return applyExclude(
    [
      { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'description', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'cpu', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'ram', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'disk', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'os', operators: SearchOperators.EQUALS_ONLY_ONLY },
      {
        preset: 'status',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
        options: statusTemplateFilter(),
      },
      {
        preset: 'preventDelete',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
        options: protectedObjectFilter(),
      },
      { preset: 'proxmoxId', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'proxmoxNode', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
    ],
    exclude,
  )
}

export function eventSearchBarFields({ exclude } = {}) {
  const t = getI18nT()
  return applyExclude(
    [
      { preset: 'name', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'slug', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'description', operators: SearchOperators.CONTAINS_ONLY },
      { preset: 'course', operators: SearchOperators.EQUALS_ONLY_ONLY },
      {
        key: 'dateStart',
        label: t('views.events.form.dateStart'),
        icon: mdiCalendar,
        type: 'date',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
      },
      {
        key: 'dateEnd',
        label: t('views.events.form.dateEnd'),
        icon: mdiCalendar,
        type: 'date',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
      },
      {
        preset: 'status',
        operators: SearchOperators.EQUALS_ONLY_ONLY,
        options: statusEventFilter(),
      },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'updatedById', operators: SearchOperators.EQUALS_ONLY_ONLY },
    ],
    exclude,
  )
}

export function mailSearchBarFields({ exclude } = {}) {
  const t = getI18nT()
  return applyExclude(
    [
      { preset: 'subject', operators: SearchOperators.CONTAINS_ONLY },
      {
        key: 'toMail',
        label: t('views.mails.columns.recipient'),
        icon: mdiEmailOutline,
        operators: SearchOperators.CONTAINS_ONLY,
      },
      { preset: 'replyTo', operators: SearchOperators.CONTAINS_ONLY },
      {
        key: 'fromName',
        label: t('views.mails.fields.fromName'),
        icon: mdiAccount,
        operators: SearchOperators.CONTAINS_ONLY,
      },
      {
        key: 'fromMail',
        label: t('views.mails.fields.fromMail'),
        icon: mdiEmailOutline,
        operators: SearchOperators.CONTAINS_ONLY,
      },
      { preset: 'event', operators: SearchOperators.EQUALS_ONLY_ONLY },
      { preset: 'createdById', operators: SearchOperators.EQUALS_ONLY_ONLY },
      {
        key: 'sendStatus',
        label: t('common.status'),
        icon: mdiListBoxOutline,
        operators: SearchOperators.EQUALS_ONLY_ONLY,
        options: [
          {
            value: 'sent',
            label: t('status.sent'),
            icon: emailStatusIcon('sent'),
          },
          {
            value: 'error',
            label: t('views.mails.filters.failed'),
            icon: emailStatusIcon('error'),
          },
          {
            value: 'queued',
            label: t('views.mails.filters.queued'),
            icon: emailStatusIcon('queued'),
          },
        ],
      },
    ],
    exclude,
  )
}
