import { marked } from 'marked'
import TurndownService from 'turndown'

/**
 * Replaces {{ ... }} template placeholders with safe tokens
 * that won't be mangled by markdown/HTML converters.
 *
 * @param {string} text - The input text
 * @returns {{ text: string, restore: (output: string) => string }}
 */
function protectPlaceholders(text) {
  const placeholders = []
  const safe = text.replace(/\{\{.*?\}\}/g, (match) => {
    const index = placeholders.length
    placeholders.push(match)
    return `TMPLVAR${index}ENDVAR`
  })
  return {
    text: safe,
    restore: (output) => {
      let result = output
      placeholders.forEach((original, i) => {
        result = result.replaceAll(`TMPLVAR${i}ENDVAR`, original)
      })
      return result
    },
  }
}

/**
 * Converts a Markdown string to HTML.
 *
 * @param {string} markdown - The Markdown source text
 * @returns {string} The generated HTML string
 */
export function markdownToHtml(markdown) {
  if (!markdown) return ''
  const { text, restore } = protectPlaceholders(markdown)
  return restore(marked(text))
}

/**
 * Converts an HTML string back to Markdown.
 *
 * @param {string} html - The HTML string to convert
 * @returns {string} The generated Markdown string
 */
export function htmlToMarkdown(html) {
  if (!html) return ''
  const { text, restore } = protectPlaceholders(html)
  const turndown = new TurndownService({
    headingStyle: 'atx',
    codeBlockStyle: 'fenced',
  })
  return restore(turndown.turndown(text))
}

/**
 * Converts an HTML string to plain text.
 * Handles line breaks, block elements, lists, and links.
 *
 * @param {string} html - The HTML string to convert
 * @returns {string} The plain text representation
 */
export function htmlToPlainText(html) {
  if (!html) return ''

  let text = html

  // Convert <br> tags to newlines
  text = text.replace(/<br\s*\/?>/gi, '\n')

  // Convert links: <a href="url">text</a> → text (url)
  text = text.replace(
    /<a\s[^>]*href=["']([^"']*)["'][^>]*>(.*?)<\/a>/gi,
    (_, href, linkText) => `${linkText} (${href})`,
  )

  // Convert list items: <li> → "- "
  text = text.replace(/<li[^>]*>/gi, '- ')

  // Add double newlines before block elements
  text = text.replace(/<\/(p|div|h[1-6]|ul|ol|blockquote|table|tr)>/gi, '\n\n')

  // Strip remaining HTML tags
  text = text.replace(/<[^>]+>/g, '')

  // Decode common HTML entities
  text = text.replace(/&amp;/g, '&')
  text = text.replace(/&lt;/g, '<')
  text = text.replace(/&gt;/g, '>')
  text = text.replace(/&quot;/g, '"')
  text = text.replace(/&#39;/g, "'")
  text = text.replace(/&nbsp;/g, ' ')

  // Clean up excessive whitespace
  text = text.replace(/\n{3,}/g, '\n\n')
  text = text.trim()

  return text
}
