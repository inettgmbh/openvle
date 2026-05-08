export default {
  name: 'TableCheckboxCell',
  template:
    '<td><input type="checkbox" @change="$emit(\'checked\', $event.target.checked)" /></td>',
  emits: ['checked'],
}
