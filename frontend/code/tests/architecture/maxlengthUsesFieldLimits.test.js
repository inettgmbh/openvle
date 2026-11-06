import { describe, expect, it } from 'vitest'

import { readdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * Architecture guard against field-length-limit drift.
 *
 * Max-character limits for a persisted, user-editable text field must have a
 * single source of truth: `src/config/fieldLimits.js` (`FIELD_LIMITS`), bound
 * to `:maxlength`. Hardcoding a numeric literal (`maxlength="50"` or
 * `:maxlength="50"`) in a form/modal reintroduces exactly the drift this system
 * removed — the same field ending up with different limits across its
 * create/edit/clone surfaces, and diverging from the DB column.
 *
 * See `patterns/centralized-field-length-limits.md` in the knowledge vault.
 *
 * This test statically forbids numeric `maxlength` literals in `.vue` files so
 * new forms cannot silently reintroduce them; use
 * `:maxlength="FIELD_LIMITS.<model>.<field>"` instead.
 */

const srcDir = join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'src')

function collectVueFiles(dir, acc = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) collectVueFiles(full, acc)
    else if (entry.name.endsWith('.vue')) acc.push(full)
  }
  return acc
}

function templateOf(source) {
  const match = source.match(/<template>([\s\S]*)<\/template>/)
  return match ? match[1] : ''
}

// Matches both the static form (`maxlength="50"`) and a bound numeric literal
// (`:maxlength="50"` / `v-bind:maxlength="50"`). A `FIELD_LIMITS`-bound
// `:maxlength="FIELD_LIMITS.event.name"` starts with a letter, so it never
// matches.
const NUMERIC_MAXLENGTH = /(?::|v-bind:)?maxlength\s*=\s*"\s*\d/

describe('maxlength uses FIELD_LIMITS guard', () => {
  const offenders = collectVueFiles(srcDir)
    .filter((file) =>
      NUMERIC_MAXLENGTH.test(templateOf(readFileSync(file, 'utf8'))),
    )
    .map((file) => file.slice(file.indexOf('/src/') + 1))

  it('no .vue file hardcodes a numeric maxlength literal', () => {
    expect(
      offenders,
      `These components hardcode a numeric \`maxlength\`, which drifts from the ` +
        `single source of truth. Bind the limit from \`@/config/fieldLimits\` ` +
        `instead: \`:maxlength="FIELD_LIMITS.<model>.<field>"\`:\n` +
        offenders.map((f) => `  - ${f}`).join('\n'),
    ).toEqual([])
  })
})
