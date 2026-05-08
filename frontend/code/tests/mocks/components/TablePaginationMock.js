export default {
  name: 'TablePagination',
  template: '<div class="pagination"></div>',
  props: ['currentPage', 'itemsTotal', 'perPage'],
  emits: ['pagination-changed'],
}
