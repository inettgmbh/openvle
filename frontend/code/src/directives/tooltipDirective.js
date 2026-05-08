/**
 * Vue directive to display a tooltip on hover.
 *
 * Usage:
 * ```html
 * <div v-tooltip="'Simple text'">Hover me</div>
 * <div v-tooltip="{ text: 'Hello', position: 'top', arrow: true }">Hover me</div>
 * <div v-tooltip.bottom="'Bottom tooltip'">Hover me</div>
 * ```
 *
 * Supports modifiers for position: `top`, `bottom`, `left`, `right`.
 * Supports optional `arrow`, `style`, and `text` properties.
 *
 * Performance: Uses a singleton tooltip element that is reused across all
 * directives. Positioning is throttled via requestAnimationFrame.
 */

// Constants
const POSITIONS = ['top', 'bottom', 'left', 'right']
const DEFAULT_POSITION = 'top'
const ARROW_SPACE = 15
const DEFAULT_SPACE = 10
const SHOW_DELAY = 120
const HIDE_DELAY = 80

const BASE_TOOLTIP_CLASSES =
  'opacity-0 absolute p-2 z-50 transition-opacity duration-150 ease-in-out pointer-events-none whitespace-pre-line max-w-xs text-left'
const DEFAULT_STYLE_CLASSES = 'bg-black text-white p-2 rounded-lg shadow-md'

const ARROW_CLASSES = {
  top: 'absolute transform rotate-45 w-4 h-4 -bottom-2 left-1/2 -translate-x-1/2 bg-inherit',
  bottom:
    'absolute transform rotate-45 w-4 h-4 -top-2 left-1/2 -translate-x-1/2 bg-inherit',
  left: 'absolute transform rotate-45 w-4 h-4 -right-2 top-1/2 -translate-y-1/2 bg-inherit',
  right:
    'absolute transform rotate-45 w-4 h-4 -left-2 top-1/2 -translate-y-1/2 bg-inherit',
}

/**
 * Determines the tooltip position from modifiers or binding value.
 *
 * @param {Object} modifiers - Vue directive modifiers object.
 * @param {string|undefined} valuePosition - Position from binding value.
 * @returns {string} The position ('top', 'bottom', 'left', or 'right').
 */
export function getPosition(modifiers = {}, valuePosition) {
  if (valuePosition && POSITIONS.includes(valuePosition)) {
    return valuePosition
  }

  for (const pos of POSITIONS) {
    if (modifiers[pos]) return pos
  }

  return DEFAULT_POSITION
}

/**
 * Extracts tooltip configuration from the binding value.
 *
 * @param {string|Object} value - The binding value (string or config object).
 * @returns {Object} Normalized configuration object.
 */
export function parseBindingValue(value) {
  if (typeof value === 'string') {
    return { text: value }
  }

  return {
    text: value?.text ?? '',
    position: value?.position,
    arrow: value?.arrow,
    style: value?.style,
  }
}

/**
 * Calculates tooltip position coordinates based on element and tooltip dimensions.
 *
 * @param {DOMRect} elRect - Bounding rect of the trigger element.
 * @param {DOMRect} tooltipRect - Bounding rect of the tooltip.
 * @param {string} position - Tooltip position ('top', 'bottom', 'left', 'right').
 * @param {number} space - Space between element and tooltip.
 * @returns {{ top: number, left: number }} Calculated coordinates.
 */
export function calculatePosition(elRect, tooltipRect, position, space) {
  const scrollX = window.scrollX
  const scrollY = window.scrollY

  switch (position) {
    case 'top':
      return {
        top: elRect.top + scrollY - tooltipRect.height - space,
        left: elRect.left + scrollX + (elRect.width - tooltipRect.width) / 2,
      }
    case 'bottom':
      return {
        top: elRect.bottom + scrollY + space,
        left: elRect.left + scrollX + (elRect.width - tooltipRect.width) / 2,
      }
    case 'left':
      return {
        top: elRect.top + scrollY + (elRect.height - tooltipRect.height) / 2,
        left: elRect.left + scrollX - tooltipRect.width - space,
      }
    case 'right':
      return {
        top: elRect.top + scrollY + (elRect.height - tooltipRect.height) / 2,
        left: elRect.right + scrollX + space,
      }
    default:
      return { top: 0, left: 0 }
  }
}

/**
 * Creates the tooltip DOM element.
 *
 * @param {string} text - Tooltip text content.
 * @param {string|undefined} customStyle - Custom CSS classes.
 * @returns {HTMLElement} The tooltip element.
 */
export function createTooltipElement(text, customStyle) {
  const tooltip = document.createElement('div')
  tooltip.className = `${BASE_TOOLTIP_CLASSES} ${customStyle || DEFAULT_STYLE_CLASSES}`
  tooltip.textContent = text
  tooltip.setAttribute('role', 'tooltip')
  return tooltip
}

/**
 * Creates the arrow element for the tooltip.
 *
 * @param {boolean|string} arrowConfig - Arrow configuration.
 * @returns {HTMLElement} The arrow element.
 */
export function createArrowElement(arrowConfig) {
  const arrow = document.createElement('div')
  if (typeof arrowConfig === 'string') {
    arrow.className = arrowConfig
  }
  return arrow
}

// ============================================================
// Singleton tooltip manager
// ============================================================

let singletonTooltip = null
let singletonArrow = null
let activeEl = null
let showTimer = null
let hideTimer = null
let rafId = null

function ensureSingleton() {
  if (!singletonTooltip) {
    singletonTooltip = document.createElement('div')
    singletonTooltip.setAttribute('role', 'tooltip')
    singletonArrow = document.createElement('div')
    singletonTooltip.appendChild(singletonArrow)
  }
}

function positionSingleton() {
  if (!activeEl || !singletonTooltip?.isConnected) return

  const config = activeEl._tooltipConfig
  if (!config) return

  const elRect = activeEl.getBoundingClientRect()
  const tooltipRect = singletonTooltip.getBoundingClientRect()
  const coords = calculatePosition(
    elRect,
    tooltipRect,
    config.position,
    config.space,
  )

  singletonTooltip.style.top = `${coords.top}px`
  singletonTooltip.style.left = `${coords.left}px`
}

function showSingleton(el) {
  clearTimeout(hideTimer)
  hideTimer = null

  const config = el._tooltipConfig
  if (!config?.text) return

  ensureSingleton()

  // If already showing for this element, skip
  if (activeEl === el && singletonTooltip.isConnected) return

  activeEl = el

  // Configure tooltip content and style
  singletonTooltip.className = `${BASE_TOOLTIP_CLASSES} ${config.customStyle || DEFAULT_STYLE_CLASSES}`
  singletonTooltip.textContent = ''

  // Arrow
  if (config.hasArrow) {
    if (typeof config.arrowConfig === 'string') {
      singletonArrow.className = config.arrowConfig
    } else {
      singletonArrow.className = ARROW_CLASSES[config.position]
    }
    singletonTooltip.appendChild(singletonArrow)
  }

  // Text node (after arrow)
  singletonTooltip.insertBefore(
    document.createTextNode(config.text),
    singletonTooltip.firstChild,
  )

  // Mount and position
  if (!singletonTooltip.isConnected) {
    document.body.appendChild(singletonTooltip)
  }

  singletonTooltip.style.position = 'absolute'
  positionSingleton()

  // Fade in
  rafId = requestAnimationFrame(() => {
    singletonTooltip.classList.remove('opacity-0')
    singletonTooltip.classList.add('opacity-100')
  })
}

function hideSingleton() {
  clearTimeout(showTimer)
  showTimer = null

  if (!singletonTooltip?.isConnected) {
    activeEl = null
    return
  }

  singletonTooltip.classList.remove('opacity-100')
  singletonTooltip.classList.add('opacity-0')

  hideTimer = setTimeout(() => {
    if (singletonTooltip?.parentNode) {
      singletonTooltip.parentNode.removeChild(singletonTooltip)
    }
    activeEl = null
  }, HIDE_DELAY)
}

// Single global scroll/resize handler with rAF throttle
let scrollRafPending = false

function onScrollOrResize() {
  if (scrollRafPending) return
  scrollRafPending = true
  requestAnimationFrame(() => {
    positionSingleton()
    scrollRafPending = false
  })
}

let globalListenersAttached = false

function attachGlobalListeners() {
  if (globalListenersAttached) return
  window.addEventListener('scroll', onScrollOrResize, { passive: true })
  window.addEventListener('resize', onScrollOrResize, { passive: true })
  globalListenersAttached = true
}

// ============================================================
// Per-element setup
// ============================================================

function setupTooltip(el, binding) {
  // Clean up previous
  if (el._tooltipCleanup) {
    el._tooltipCleanup()
  }

  if (binding.value === undefined || binding.value === null) return

  const config = parseBindingValue(binding.value)
  if (!config.text) return

  const position = getPosition(binding.modifiers, config.position)
  const hasArrow = config.arrow !== undefined && config.arrow !== false
  const space = hasArrow ? ARROW_SPACE : DEFAULT_SPACE

  // Store config on element for singleton access
  el._tooltipConfig = {
    text: config.text,
    position,
    hasArrow,
    arrowConfig: config.arrow,
    customStyle: config.style,
    space,
  }

  attachGlobalListeners()

  function onMouseEnter() {
    clearTimeout(hideTimer)
    showTimer = setTimeout(() => showSingleton(el), SHOW_DELAY)
  }

  function onMouseLeave() {
    clearTimeout(showTimer)
    showTimer = null
    hideSingleton()
  }

  el.addEventListener('mouseenter', onMouseEnter)
  el.addEventListener('mouseleave', onMouseLeave)

  el._tooltipCleanup = () => {
    clearTimeout(showTimer)
    clearTimeout(hideTimer)
    if (activeEl === el) {
      hideSingleton()
    }
    el.removeEventListener('mouseenter', onMouseEnter)
    el.removeEventListener('mouseleave', onMouseLeave)
    delete el._tooltipConfig
  }
}

export default {
  /**
   * Called when the directive is mounted.
   *
   * @param {HTMLElement} el - The element the directive is bound to.
   * @param {DirectiveBinding} binding - The binding value passed to the directive.
   */
  mounted(el, binding) {
    setupTooltip(el, binding)
  },

  /**
   * Called when the component is updated.
   *
   * @param {HTMLElement} el - The element the directive is bound to.
   * @param {DirectiveBinding} binding - The binding value passed to the directive.
   */
  updated(el, binding) {
    setupTooltip(el, binding)
  },

  /**
   * Called before the component is unmounted.
   *
   * @param {HTMLElement} el - The element the directive is bound to.
   */
  beforeUnmount(el) {
    if (el._tooltipCleanup) {
      el._tooltipCleanup()
    }
  },
}
