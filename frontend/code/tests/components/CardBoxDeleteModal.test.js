import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'

import CardBoxDeleteModal from '@/components/CardBoxDeleteModal.vue'

// Writes the tooltip content into an attribute so tests can assert it;
// the global setup registers `tooltip` only as a no-op.
const tooltipStub = {
  mounted(el, binding) {
    el.setAttribute('data-tooltip', binding.value ?? '')
  },
  updated(el, binding) {
    el.setAttribute('data-tooltip', binding.value ?? '')
  },
}

const stubs = {
  OverlayLayer: { template: '<div class="overlay"><slot /></div>' },
  CardBox: {
    template: '<div class="card-box"><slot /><slot name="footer" /></div>',
  },
  CardBoxComponentTitle: {
    template: '<div class="card-title"><slot /></div>',
    props: ['title'],
  },
  BaseButton: {
    template:
      '<button class="base-button" :disabled="disabled" @click="$emit(\'click\', $event)">{{ label }}</button>',
    emits: ['click'],
    props: [
      'label',
      'icon',
      'color',
      'small',
      'roundedFull',
      'disabled',
      'type',
    ],
  },
  BaseButtons: { template: '<div><slot /></div>' },
  FormField: { template: '<div class="form-field"><slot /></div>' },
  FormControl: {
    template:
      '<input class="form-control" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
    props: ['modelValue', 'icon', 'placeholder'],
    emits: ['update:modelValue', 'set-ref'],
  },
}

const mountModal = (props = {}) =>
  mount(CardBoxDeleteModal, {
    props: {
      modelValue: true,
      name: 'Test Umgebung',
      checkvalue: 'Test Umgebung',
      ...props,
    },
    global: { stubs, directives: { tooltip: tooltipStub } },
  })

const findConfirmButton = (w) =>
  w.findAll('button.base-button').find((b) => b.text() === 'Löschen')

describe('CardBoxDeleteModal', () => {
  let wrapper

  afterEach(() => {
    wrapper?.unmount()
  })

  it('enables confirm only after typing the checkvalue', async () => {
    wrapper = mountModal()

    const btn = findConfirmButton(wrapper)
    expect(btn.attributes('disabled')).toBeDefined()

    await wrapper.find('input.form-control').setValue('Test Umgebung')
    expect(btn.attributes('disabled')).toBeUndefined()
  })

  it('keeps confirm disabled and hides the name confirmation when blocked', () => {
    wrapper = mountModal({ blocked: true })

    expect(findConfirmButton(wrapper).attributes('disabled')).toBeDefined()
    // The name-typing section is pointless while blocked and must not render
    expect(wrapper.find('input.form-control').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Zur Bestätigung bitte eingeben:')
  })

  it('shows the blocked tooltip on the disabled confirm button', () => {
    wrapper = mountModal({ blocked: true })

    expect(findConfirmButton(wrapper).attributes('data-tooltip')).toBe(
      'Löschen nicht möglich, solange zugeordnete Objekte existieren',
    )
  })

  it('renders the info hint as info NotificationBar', () => {
    wrapper = mountModal({
      info: 'Changelogs, Berechtigungen und Tags werden automatisch mitgelöscht.',
    })

    expect(wrapper.text()).toContain(
      'Changelogs, Berechtigungen und Tags werden automatisch mitgelöscht.',
    )
    // colorsBgLight.info from src/colors.js
    expect(wrapper.html()).toContain('bg-blue-500')
  })

  it('renders the warning as danger NotificationBar when blocked', () => {
    wrapper = mountModal({
      blocked: true,
      warning: 'Diese Umgebung wird noch verwendet.',
    })

    expect(wrapper.text()).toContain('Diese Umgebung wird noch verwendet.')
    // colorsBgLight.danger from src/colors.js
    expect(wrapper.html()).toContain('bg-red-500')
    expect(wrapper.html()).not.toContain('bg-yellow-500')
  })

  it('renders the warning as warning NotificationBar when not blocked', () => {
    wrapper = mountModal({ warning: 'Nur ein Hinweis.' })

    expect(wrapper.text()).toContain('Nur ein Hinweis.')
    // colorsBgLight.warning from src/colors.js
    expect(wrapper.html()).toContain('bg-yellow-500')
  })

  it('renders related items with label and total count badge', () => {
    wrapper = mountModal({
      blocked: true,
      warning: 'Diese Umgebung wird noch verwendet.',
      relatedLabel: 'Zugeordnete Veranstaltungen:',
      relatedCount: 8,
      relatedItems: [
        { label: 'Veranstaltung A' },
        { label: '… und 7 weitere Veranstaltungen' },
      ],
    })

    expect(wrapper.text()).toContain('Zugeordnete Veranstaltungen:')
    expect(wrapper.text()).toContain('Veranstaltung A')
    expect(wrapper.text()).toContain('… und 7 weitere Veranstaltungen')
    // Badge shows the total, not the number of rendered rows
    expect(wrapper.text()).toContain('8')
  })

  it('falls back to the item count in the badge without relatedCount', () => {
    wrapper = mountModal({
      relatedLabel: 'Zugeordnete Veranstaltungen:',
      relatedItems: [
        { label: 'Veranstaltung A' },
        { label: 'Veranstaltung B' },
      ],
    })

    expect(wrapper.text()).toContain('2')
  })
})
