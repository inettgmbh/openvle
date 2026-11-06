import {
  mdiShieldAlert,
  mdiShieldCheck,
  mdiShieldHalfFull,
  mdiShieldOff,
  mdiShieldOffOutline,
  mdiShieldOutline,
  mdiShieldSync,
} from '@mdi/js'
import { describe, expect, it } from 'vitest'

import { haStateIconVM } from '@/utils/icons'

const TRANSIENT_STATES = [
  'migrate',
  'relocate',
  'recovery',
  'request_start',
  'request_stop',
  'queued',
  'freeze',
]

describe('haStateIconVM', () => {
  it.each([
    ['started', mdiShieldCheck],
    ['stopped', mdiShieldOutline],
    ['disabled', mdiShieldOff],
    ['ignored', mdiShieldOffOutline],
    ['error', mdiShieldAlert],
    ['fence', mdiShieldAlert],
  ])('maps %s to the expected icon', (state, icon) => {
    expect(haStateIconVM(state)).toBe(icon)
  })

  it.each(TRANSIENT_STATES)(
    'maps transient state %s to the sync icon',
    (state) => {
      expect(haStateIconVM(state)).toBe(mdiShieldSync)
    },
  )

  it('always returns a fallback icon for unknown states', () => {
    expect(haStateIconVM('some_future_state')).toBe(mdiShieldHalfFull)
    expect(haStateIconVM(null)).toBe(mdiShieldHalfFull)
    expect(haStateIconVM(undefined)).toBe(mdiShieldHalfFull)
  })

  it('is case-insensitive', () => {
    expect(haStateIconVM('STARTED')).toBe(mdiShieldCheck)
  })
})
