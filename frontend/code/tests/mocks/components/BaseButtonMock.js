export default {
  name: 'BaseButton',
  template:
    '<button :disabled="disabled" @click="$emit(\'click\', $event)" @auxclick="$emit(\'auxclick\', $event)"><slot /></button>',
  props: ['color', 'icon', 'small', 'disabled', 'loading', 'type', 'label'],
  emits: ['click', 'auxclick'],
}
