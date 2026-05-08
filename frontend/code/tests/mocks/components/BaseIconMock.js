export default {
  name: 'BaseIcon',
  template: '<span class="icon" @click="handleClick"></span>',
  props: ['path', 'w', 'h', 'fill', 'iconsize', 'viewBox', 'size'],
  emits: ['click'],
  methods: {
    handleClick(event) {
      this.$emit('click', event)
    },
  },
}
