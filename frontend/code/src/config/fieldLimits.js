/**
 * Central, per-object-model field length limits (max characters).
 *
 * Single source of truth for the FRONTEND. Bind these to `:maxlength` on
 * FormControls (and use them in any client-side validation) instead of
 * hardcoding magic numbers in individual forms/modals — so the same field has
 * the same limit across every view where it is created or edited.
 *
 * Scope: frontend enforcement only for now. When we later centralize on the
 * backend, mirror these values in a Python module and add a parity test that
 * asserts `limit <= DB column length` (the DB column is the hard ceiling; these
 * app limits must stay at or below it).
 */
export const FIELD_LIMITS = Object.freeze({
  event: Object.freeze({
    // name is intentionally <= its VARCHAR(50) column and small enough to
    // bound the derived Guacamole connection name.
    name: 35,
    slug: 8,
    description: 1000,
  }),
  user: Object.freeze({
    name: 256,
    email: 254,
    // DB column is VARCHAR(25); kept in sync with the backend for now even
    // though e-mail-as-username is desired (tracked separately).
    username: 25,
  }),
  role: Object.freeze({
    name: 255,
    key: 255,
    description: 1000,
  }),
  course: Object.freeze({
    name: 255,
    description: 1000,
  }),
  os: Object.freeze({
    name: 100,
    description: 1000,
  }),
  application: Object.freeze({
    name: 255,
    description: 1000,
  }),
  vendor: Object.freeze({
    name: 100,
    description: 1000,
  }),
  tag: Object.freeze({
    // DB columns are wider (key 50 / value 100); the tighter 20/20 UI limit is
    // the historical enforced value, preserved as the single source.
    key: 20,
    value: 20,
  }),
  policy: Object.freeze({
    name: 40,
    description: 1000,
  }),
  template: Object.freeze({
    // name DB column is VARCHAR(100); the historical enforced value of 50 is kept.
    name: 50,
    // description is a BaseMarkdown field backed by VARCHAR(1000) (DescriptionMixin);
    // capped at the column to prevent silent truncation.
    description: 1000,
  }),
  vm: Object.freeze({
    // name DB column is VARCHAR(100); flows into the derived Guacamole name (100),
    // so the historical enforced value of 50 is kept as a conservative interim.
    name: 50,
    // description is a BaseMarkdown field backed by VARCHAR(1000) (DescriptionMixin).
    description: 1000,
    // HA retry/relocate counts (Proxmox max_restart/max_relocate) have no DB
    // column; 2 digits (0-99) is a sane UI bound for these numeric inputs.
    haMaxRestart: 2,
    haMaxRelocate: 2,
  }),
  mailtemplate: Object.freeze({
    name: 100,
    subject: 150,
    replyTo: 254,
    description: 1000,
  }),
  mail: Object.freeze({
    subject: 150,
    fromName: 50,
    fromMail: 254,
    replyTo: 254,
  }),
  guacamole: Object.freeze({
    name: 100,
  }),
  system: Object.freeze({
    value: 250,
  }),
  connectionprofile: Object.freeze({
    // username/password flow into derived connection names (downstream budget);
    // conservative interim values matching the DB columns.
    username: 50,
    password: 50,
  }),
})

/**
 * Central numeric VALUE bounds for number inputs (max allowed value, not
 * character count — see FIELD_LIMITS above for those). Bind these to `:max`
 * on numeric FormControls and reuse them in client-side validation.
 */
export const FIELD_VALUE_LIMITS = Object.freeze({
  vm: Object.freeze({
    // Proxmox HA retry/relocate counts; capped to a sane operational range.
    haMaxRestart: 20,
    haMaxRelocate: 20,
  }),
})
