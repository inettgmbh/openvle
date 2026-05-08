export default {
  name: 'TableSearchBar',
  template: '<div class="table-search-bar"></div>',
  props: [
    'fields',
    'maxFilters',
    'objectModel',
    'placeholder',
    'initialFilters',
    'syncQuery',
    'queryKey',
  ],
  emits: ['filtersChanged'],
  setup(_, { expose }) {
    const clearAll = () => {}
    const focus = () => {}
    expose({ clearAll, focus })
  },
}
