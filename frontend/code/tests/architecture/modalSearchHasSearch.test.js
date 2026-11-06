import { describe, expect, it } from 'vitest'

import { readdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * Architecture guard against a recurring visual bug.
 *
 * The search-results dropdown (`SearchField.vue`) is an absolutely-positioned
 * `<ul>` in the normal DOM flow — it is NOT teleported. Any ancestor with
 * `overflow != visible` therefore clips it, and z-index cannot defeat overflow
 * clipping.
 *
 * A modal body gets `overflow-y-auto` whenever it is a modal WITHOUT the
 * `has-search` opt-out (see `CardBoxComponentBody.vue` and `CardBoxModal.vue`).
 * So any modal that embeds a `<SearchControl>` / `<SearchField>` MUST set
 * `has-search`, otherwise the dropdown is clipped inside the modal instead of
 * overlaying it.
 *
 * This test statically enforces that invariant so the bug (originally in the
 * "add participant" modal, and latently in the "create object permission"
 * modal) cannot silently reappear in a new modal.
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

const hasSearchComponent = (tpl) =>
  /<SearchControl[\s>]/.test(tpl) || /<SearchField[\s>]/.test(tpl)

const rendersModal = (tpl) =>
  /<CardBoxModal[\s>]/.test(tpl) || /\bis-modal\b/.test(tpl)

const optsOutOfClipping = (tpl) => /(?:^|\s):?has-search\b/.test(tpl)

describe('modal search dropdown clipping guard', () => {
  const offenders = collectVueFiles(srcDir)
    .filter((file) => {
      const tpl = templateOf(readFileSync(file, 'utf8'))
      return hasSearchComponent(tpl) && rendersModal(tpl)
    })
    .filter(
      (file) => !optsOutOfClipping(templateOf(readFileSync(file, 'utf8'))),
    )
    .map((file) => file.slice(file.indexOf('/src/') + 1))

  it('every modal containing a search sets `has-search` to avoid clipping the dropdown', () => {
    expect(
      offenders,
      `These components render a search inside a modal but do not set \`has-search\`, ` +
        `so the results dropdown will be clipped by the modal's \`overflow-y-auto\`. ` +
        `Add \`has-search\` to the <CardBoxModal> / <CardBox is-modal> element:\n` +
        offenders.map((f) => `  - ${f}`).join('\n'),
    ).toEqual([])
  })
})
