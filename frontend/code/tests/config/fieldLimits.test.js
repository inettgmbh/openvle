import { describe, expect, it } from 'vitest'

import { FIELD_LIMITS, FIELD_VALUE_LIMITS } from '@/config/fieldLimits'

describe('FIELD_LIMITS', () => {
  it('is deeply frozen so limits cannot be mutated at runtime', () => {
    expect(Object.isFrozen(FIELD_LIMITS)).toBe(true)
    for (const model of Object.values(FIELD_LIMITS)) {
      expect(Object.isFrozen(model)).toBe(true)
    }
  })

  it('exposes only positive integer limits', () => {
    for (const [model, fields] of Object.entries(FIELD_LIMITS)) {
      for (const [field, limit] of Object.entries(fields)) {
        expect(
          Number.isInteger(limit) && limit > 0,
          `${model}.${field} must be a positive integer, got ${limit}`,
        ).toBe(true)
      }
    }
  })

  // Documents every model's limits — a change here must be deliberate. Values
  // stay <= the backing DB column (headroom principle); some are tighter because
  // the value flows into a length-bounded derived string (e.g. names feeding the
  // Guacamole connection name). template/vm description are BaseMarkdown fields
  // backed by VARCHAR(1000); policy/mailtemplate content are TEXT columns and stay
  // unbounded (no tight DB ceiling), so they are intentionally absent here.
  it('pins the field limits for every model', () => {
    expect(FIELD_LIMITS).toEqual({
      event: { name: 35, slug: 8, description: 1000 },
      user: { name: 256, email: 254, username: 25 },
      role: { name: 255, key: 255, description: 1000 },
      course: { name: 255, description: 1000 },
      os: { name: 100, description: 1000 },
      application: { name: 255, description: 1000 },
      vendor: { name: 100, description: 1000 },
      tag: { key: 20, value: 20 },
      policy: { name: 40, description: 1000 },
      template: { name: 50, description: 1000 },
      vm: { name: 50, description: 1000, haMaxRestart: 2, haMaxRelocate: 2 },
      mailtemplate: {
        name: 100,
        subject: 150,
        replyTo: 254,
        description: 1000,
      },
      mail: { subject: 150, fromName: 50, fromMail: 254, replyTo: 254 },
      guacamole: { name: 100 },
      system: { value: 250 },
      connectionprofile: { username: 50, password: 50 },
    })
  })
})

describe('FIELD_VALUE_LIMITS', () => {
  it('is deeply frozen so limits cannot be mutated at runtime', () => {
    expect(Object.isFrozen(FIELD_VALUE_LIMITS)).toBe(true)
    for (const model of Object.values(FIELD_VALUE_LIMITS)) {
      expect(Object.isFrozen(model)).toBe(true)
    }
  })

  it('exposes only positive integer limits', () => {
    for (const [model, fields] of Object.entries(FIELD_VALUE_LIMITS)) {
      for (const [field, limit] of Object.entries(fields)) {
        expect(
          Number.isInteger(limit) && limit > 0,
          `${model}.${field} must be a positive integer, got ${limit}`,
        ).toBe(true)
      }
    }
  })

  // Documents every numeric value bound — a change here must be deliberate.
  it('pins the value limits for every model', () => {
    expect(FIELD_VALUE_LIMITS).toEqual({
      vm: { haMaxRestart: 20, haMaxRelocate: 20 },
    })
  })
})
