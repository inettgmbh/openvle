import { reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/**
 * Composable to manage pagination, sorting, searching, and deletion logic for a list view.
 *
 * This utility integrates with Vue Router to optionally sync query parameters (`page`, `perPage`, `sort`, etc.)
 * and provides state + handler methods for use in paginated tables or list components.
 *
 * @param {Object} [options={}] - Optional configuration.
 * @param {number} [options.initialPage=1] - Initial page number if not in route query.
 * @param {number} [options.initialPerPage=10] - Initial items per page.
 * @param {string|null} [options.initialSortColumn=null] - Initial sort column key.
 * @param {'asc'|'desc'|null} [options.initialSortOrder=null] - Initial sort order.
 * @param {string|null} [options.initialSearchField=null] - Initial field used for search.
 * @param {string|null} [options.initialSearchValue=null] - Initial value used for search.
 * @param {() => void} [options.fetch] - Optional fetch callback triggered on state changes.
 * @param {boolean} [options.useReplace=false] - Whether to use `router.replace` instead of `router.push` for query updates.
 * @param {boolean} [options.syncQuery=true] - Whether to sync pagination/sort/search state to the URL query.
 *
 * @returns {Object} List state and handlers:
 * @returns {import('vue').Ref<number>} return.currentPage - Current page index.
 * @returns {import('vue').Ref<number>} return.perPage - Items per page.
 * @returns {import('vue').Ref<string|null>} return.sortColumnKey - Key of the column to sort by.
 * @returns {import('vue').Ref<'asc'|'desc'|null>} return.sortDirection - Sort direction.
 * @returns {import('vue').Ref<string|null>} return.searchField - Search field key.
 * @returns {import('vue').Ref<string|null>} return.searchValue - Search input value.
 * @returns {import('vue').Ref<any>} return.objToRemove - Object pending deletion.
 * @returns {Object<string, import('vue').Ref<boolean>>} return.modals - Reactive modal visibility map (e.g. `deleteObject`).
 *
 * @returns {Function} return.handlePaginationChanged - Updates pagination and triggers `fetch`.
 * @returns {Function} return.handleSortOrderChanged - Updates sort parameters and triggers `fetch`.
 * @returns {Function} return.handleSearch - Applies search criteria and triggers `fetch`.
 * @returns {Function} return.handleDeleteObject - Sets `objToRemove` and opens the deletion modal.
 */
export function usePaginationList(options = {}) {
  const route = useRoute()
  const router = useRouter()

  const {
    initialPage = 1,
    initialPerPage = 10,
    initialSortColumn = null,
    initialSortOrder = null,
    initialSearchField = null,
    initialSearchValue = null,
    fetch,
    useReplace = false,
    syncQuery = true,
  } = options

  const toInt = (v, fallback) => {
    const n = parseInt(v, 10)
    return Number.isFinite(n) ? n : fallback
  }

  const currentPage = ref(toInt(route.query.page, initialPage))
  const perPage = ref(toInt(route.query.perPage, initialPerPage))

  const sortColumnKey = ref(route.query.sort ?? initialSortColumn)
  const sortDirection = ref(route.query.order ?? initialSortOrder)

  const searchField = ref(route.query.searchField ?? initialSearchField)
  const searchValue = ref(route.query.searchValue ?? initialSearchValue)

  const objToRemove = ref(null)
  const modals = {
    deleteObject: ref(false),
  }

  const cleanQuery = (q) =>
    Object.fromEntries(
      Object.entries(q).filter(
        ([_, v]) => v !== undefined && v !== null && v !== '',
      ),
    )

  const navigate = useReplace ? router.replace : router.push

  const maybeSync = async (patch) => {
    if (!syncQuery) return
    const next = cleanQuery({ ...route.query, ...patch })
    const same =
      Object.keys(next).length === Object.keys(route.query).length &&
      Object.entries(next).every(([k, v]) => route.query[k] === v)
    if (!same) await navigate({ query: next })
  }

  let fetchTriggered = false

  const fetchIf = () => {
    if (typeof fetch === 'function') fetch()
  }

  const handlePaginationChanged = (newPage, newPerPage) => {
    currentPage.value = newPage
    if (perPage.value != newPerPage) {
      currentPage.value = 1
    }
    perPage.value = newPerPage
    maybeSync({ page: currentPage.value, perPage: newPerPage })
    fetchIf()
  }

  const handleSortOrderChanged = (newSortOrder, newSortColumn) => {
    sortColumnKey.value = newSortColumn
    sortDirection.value = newSortOrder
    maybeSync({ sort: newSortColumn, order: newSortOrder })
    fetchIf()
  }

  const handleSearch = ({ field, value }) => {
    searchField.value = field
    searchValue.value = value
    currentPage.value = 1
    // Search filter sync is handled by useSearchQuerySync in TableSearchBar — only page reset needed here
    maybeSync({ page: 1 })
    fetchTriggered = true
    fetchIf()
  }

  // Call in onMounted to trigger an immediate fetch when no URL filters are present.
  // If TableSearchBar already triggered a fetch via handleSearch, this is a no-op.
  const initialFetch = () => {
    if (!fetchTriggered) {
      fetchIf()
    }
  }

  const handleDeleteObject = (object) => {
    objToRemove.value = object
    modals.deleteObject.value = true
  }

  if (syncQuery) {
    watch(
      () => [
        route.query.page,
        route.query.perPage,
        route.query.sort,
        route.query.order,
        route.query.searchField,
        route.query.searchValue,
      ],
      ([qPage, qPerPage, qSort, qOrder, qSField, qSValue]) => {
        if (qPage != null) currentPage.value = toInt(qPage, initialPage)
        if (qPerPage != null) perPage.value = toInt(qPerPage, initialPerPage)
        if (qSort !== undefined) sortColumnKey.value = qSort ?? null
        if (qOrder !== undefined) sortDirection.value = qOrder ?? null
        if (qSField !== undefined) searchField.value = qSField ?? null
        if (qSValue !== undefined) searchValue.value = qSValue ?? null
      },
    )
  }

  return {
    currentPage,
    perPage,
    sortColumnKey,
    sortDirection,
    searchField,
    searchValue,
    objToRemove,
    modals,
    handlePaginationChanged,
    handleSortOrderChanged,
    handleSearch,
    handleDeleteObject,
    initialFetch,
  }
}

/**
 * Composable to manage pagination, sorting, deletion, and lazy-loading behavior for child components.
 *
 * Designed for use in tabbed or dynamic views, where multiple child components need independent
 * pagination and sorting logic, modal triggering, and fetch operations.
 *
 * @param {Object} [options={}] - Configuration options.
 * @param {Array<Object>} [options.children] - Array of child component objects, each with at least a `name` and optionally `fetchData`, `currentPage`, `perPage`, etc.
 * @param {() => any[]} [options.fetchArgs=() => []] - Function returning arguments to pass to all fetch functions.
 * @param {Object<string, import('vue').Ref<boolean>>} [options.modals] - Optional map of modal visibility refs, keyed by modal name.
 * @param {import('vue').Ref<any>} [options.objToRemove] - Optional ref where the object to delete will be stored before modal confirmation.
 * @param {Object} [options.route] - Vue Router route object, used to check URL query params for search bar sync.
 *
 * @returns {Object} Pagination and tab handling state and methods:
 * @returns {import('vue').Ref<Array<Object>>} return.childComponents - Reactive list of child component configs.
 * @returns {Set<string>} return.loadedTabs - Tracks tabs that have already fetched their data.
 * @returns {Function} return.handlePaginationChanged - Updates current page and per-page settings for a component and triggers refetch.
 * @returns {Function} return.handleSortOrderChanged - Updates sort direction and column for a component and triggers refetch.
 * @returns {Function} return.handleSearch - Updates search field/value for a component, resets to page 1, and triggers refetch.
 * @returns {Function} return.handleDeleteObject - Stores the object to delete and shows the corresponding modal.
 * @returns {Function} return.handleTabChanged - Triggers lazy loading for a tab if not already loaded.
 */
export function usePaginationChild(options = {}) {
  const { children, fetchArgs = () => [], modals, objToRemove, route } = options

  const childComponents = ref(children)
  const loadedTabs = reactive(new Set())

  const findIndex = (name) =>
    childComponents.value.findIndex((c) => c.name === name)

  const findFetch = (name) =>
    childComponents.value.find((c) => c.name === name)?.fetchData

  const handlePaginationChanged = (newPage, newPerPage, componentName) => {
    const i = findIndex(componentName)
    if (i !== -1) {
      childComponents.value[i].currentPage = newPage
      if (childComponents.value[i].perPage !== newPerPage) {
        childComponents.value[i].currentPage = 1
      }
      childComponents.value[i].perPage = newPerPage
    }
    const fn = findFetch(componentName)
    if (fn) fn(...fetchArgs())
  }

  const handleSortOrderChanged = (
    newSortOrder,
    newSortColumn,
    componentName,
  ) => {
    const i = findIndex(componentName)
    if (i !== -1) {
      childComponents.value[i].sortColumnKey = newSortColumn
      childComponents.value[i].sortDirection = newSortOrder
    }
    const fn = findFetch(componentName)
    if (fn) fn(...fetchArgs())
  }

  const handleSearch = ({ field, value, objectModel }) => {
    const componentName = objectModel
    const i = findIndex(componentName)
    if (i !== -1) {
      childComponents.value[i].searchField = field
      childComponents.value[i].searchValue = value
      childComponents.value[i].currentPage = 1
    }
    const fn = findFetch(componentName)
    if (fn) fn(...fetchArgs())
  }

  const handleDeleteObject = (object, componentName) => {
    if (objToRemove) objToRemove.value = object
    const modalKey =
      'delete' + componentName.charAt(0).toUpperCase() + componentName.slice(1)
    const modal = modals?.[modalKey]
    if (modal) modal.value = true
  }

  let activeTab = null

  const handleTabChanged = async (tabId) => {
    activeTab = tabId
    if (loadedTabs.has(tabId)) return
    loadedTabs.add(tabId)

    // If the tab has a search bar with URL sync and filters exist in the URL,
    // skip the initial fetch — the TableSearchBar will restore filters and
    // trigger the fetch via handleSearch, avoiding a duplicate API call.
    // Convention: query key is `filter-${tabId}` (matching BaseTable's default).
    const child = childComponents.value.find((c) => c.name === tabId)
    const queryKey = child?.searchBarQueryKey ?? `filter-${tabId}`
    if (child?.searchField !== undefined && route?.query[queryKey]) {
      return
    }

    const fn = findFetch(tabId)
    if (fn) fn(...fetchArgs())
  }

  const refreshActiveTab = () => {
    if (!activeTab || !loadedTabs.has(activeTab)) return
    const fn = findFetch(activeTab)
    if (fn) fn(...fetchArgs())
  }

  return {
    childComponents,
    loadedTabs,
    handlePaginationChanged,
    handleSortOrderChanged,
    handleSearch,
    handleDeleteObject,
    handleTabChanged,
    refreshActiveTab,
  }
}
