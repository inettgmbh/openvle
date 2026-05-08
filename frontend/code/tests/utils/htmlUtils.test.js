import { describe, expect, it } from 'vitest'

import {
  htmlToMarkdown,
  htmlToPlainText,
  markdownToHtml,
} from '@/utils/htmlUtils'

describe('markdownToHtml', () => {
  it('returns empty string for falsy input', () => {
    expect(markdownToHtml('')).toBe('')
    expect(markdownToHtml(null)).toBe('')
    expect(markdownToHtml(undefined)).toBe('')
  })

  it('converts basic markdown to HTML', () => {
    expect(markdownToHtml('**bold**')).toContain('<strong>bold</strong>')
    expect(markdownToHtml('*italic*')).toContain('<em>italic</em>')
    expect(markdownToHtml('# Heading')).toContain('<h1>Heading</h1>')
  })

  it('converts a link without placeholders', () => {
    const html = markdownToHtml('[hier](https://example.com)')
    expect(html).toContain('<a href="https://example.com">hier</a>')
  })

  it('converts a link with a placeholder in URL', () => {
    const md = '[hier](https://example.com/#/events/{{ event.id }})'
    const html = markdownToHtml(md)
    expect(html).toContain('href="https://example.com/#/events/{{ event.id }}"')
    expect(html).toContain('>hier</a>')
    expect(html).not.toContain('%7B')
    expect(html).not.toContain('%7D')
  })

  it('converts a link with a placeholder in text', () => {
    const md = '[{{ event.name }}](https://example.com)'
    const html = markdownToHtml(md)
    expect(html).toContain('>{{ event.name }}</a>')
  })

  it('converts a link with placeholders in both URL and text', () => {
    const md = '[{{ event.name }}](https://example.com/#/events/{{ event.id }})'
    const html = markdownToHtml(md)
    expect(html).toContain('href="https://example.com/#/events/{{ event.id }}"')
    expect(html).toContain('>{{ event.name }}</a>')
  })

  it('converts an image with a placeholder in URL', () => {
    const md = '![Alt](https://example.com/{{ event.id }}/img.png)'
    const html = markdownToHtml(md)
    expect(html).toContain('src="https://example.com/{{ event.id }}/img.png"')
    expect(html).not.toContain('%7B')
  })

  it('preserves placeholder with underscores in text', () => {
    const html = markdownToHtml('Name: {{ event_name }}')
    expect(html).toContain('{{ event_name }}')
    expect(html).not.toContain('event\\_name')
  })

  it('preserves placeholder with underscores inside bold', () => {
    const html = markdownToHtml('**{{ event_name }}**')
    expect(html).toContain('<strong>{{ event_name }}</strong>')
  })

  it('preserves placeholder inside inline code', () => {
    const html = markdownToHtml('`{{ event.id }}`')
    expect(html).toContain('<code>{{ event.id }}</code>')
  })

  it('preserves placeholders inside a heading', () => {
    const html = markdownToHtml('# {{ event.name }}')
    expect(html).toContain('<h1>{{ event.name }}</h1>')
  })

  it('preserves placeholders inside list items', () => {
    const html = markdownToHtml('- {{ event.name }}\n- {{ user.name }}')
    expect(html).toContain('<li>{{ event.name }}</li>')
    expect(html).toContain('<li>{{ user.name }}</li>')
  })

  it('preserves multiple placeholders in the same line', () => {
    const md = 'Hallo {{ user.name }}, Event {{ event.name }}.'
    const html = markdownToHtml(md)
    expect(html).toContain('{{ user.name }}')
    expect(html).toContain('{{ event.name }}')
  })

  it('handles mixed content with links and text placeholders', () => {
    const md =
      'Hallo {{ user.name }}, Details [hier](https://example.com/{{ event.id }}).'
    const html = markdownToHtml(md)
    expect(html).toContain('{{ user.name }}')
    expect(html).toContain('href="https://example.com/{{ event.id }}"')
    expect(html).toContain('>hier</a>')
  })
})

describe('htmlToMarkdown', () => {
  it('returns empty string for falsy input', () => {
    expect(htmlToMarkdown('')).toBe('')
    expect(htmlToMarkdown(null)).toBe('')
    expect(htmlToMarkdown(undefined)).toBe('')
  })

  it('converts basic HTML to markdown', () => {
    expect(htmlToMarkdown('<strong>bold</strong>')).toBe('**bold**')
    expect(htmlToMarkdown('<em>italic</em>')).toBe('_italic_')
    expect(htmlToMarkdown('<h1>Heading</h1>')).toBe('# Heading')
  })

  it('converts a link without placeholders', () => {
    const md = htmlToMarkdown(
      '<p>Infos <a href="https://example.com">hier</a>.</p>',
    )
    expect(md).toContain('[hier](https://example.com)')
  })

  it('preserves a placeholder in href attribute', () => {
    const html =
      '<p>Infos <a href="https://example.com/#/events/{{ event.id }}">hier</a>.</p>'
    const md = htmlToMarkdown(html)
    expect(md).toContain('[hier](https://example.com/#/events/{{ event.id }})')
  })

  it('preserves a placeholder in link text', () => {
    const md = htmlToMarkdown(
      '<p><a href="https://example.com">{{ event.name }}</a></p>',
    )
    expect(md).toContain('[{{ event.name }}](https://example.com)')
  })

  it('preserves a placeholder in img src', () => {
    const md = htmlToMarkdown(
      '<p><img src="https://example.com/{{ event.id }}/img.png" alt="Alt"></p>',
    )
    expect(md).toContain('https://example.com/{{ event.id }}/img.png')
  })

  it('does not escape underscores inside placeholders', () => {
    const md = htmlToMarkdown('<p>{{ event_name }}</p>')
    expect(md).toContain('{{ event_name }}')
    expect(md).not.toContain('event\\_name')
  })

  it('does not escape underscores inside bold placeholders', () => {
    const md = htmlToMarkdown('<p><strong>{{ event_name }}</strong></p>')
    expect(md).toContain('{{ event_name }}')
    expect(md).not.toContain('event\\_name')
  })

  it('does not escape underscores inside italic placeholders', () => {
    const md = htmlToMarkdown('<p><em>{{ event_name }}</em></p>')
    expect(md).toContain('{{ event_name }}')
    expect(md).not.toContain('event\\_name')
  })

  it('preserves multiple placeholders with underscores', () => {
    const md = htmlToMarkdown(
      '<p>Name: {{ event_name }}, ID: {{ event_id }}</p>',
    )
    expect(md).toContain('{{ event_name }}')
    expect(md).toContain('{{ event_id }}')
    expect(md).not.toContain('event\\_name')
    expect(md).not.toContain('event\\_id')
  })

  it('handles mixed content with links and text placeholders', () => {
    const html =
      '<p>Hallo {{ user.name }}, Details <a href="https://example.com/{{ event.id }}">hier</a>.</p>'
    const md = htmlToMarkdown(html)
    expect(md).toContain('{{ user.name }}')
    expect(md).toContain('[hier](https://example.com/{{ event.id }})')
  })
})

describe('htmlToPlainText', () => {
  it('returns empty string for falsy input', () => {
    expect(htmlToPlainText('')).toBe('')
    expect(htmlToPlainText(null)).toBe('')
    expect(htmlToPlainText(undefined)).toBe('')
  })

  it('converts basic HTML to plain text', () => {
    expect(htmlToPlainText('<p>Hello World</p>')).toBe('Hello World')
  })

  it('converts links to text (url) format', () => {
    const plain = htmlToPlainText(
      '<p><a href="https://example.com">hier</a></p>',
    )
    expect(plain).toBe('hier (https://example.com)')
  })

  it('preserves placeholders in link href', () => {
    const plain = htmlToPlainText(
      '<p><a href="https://example.com/{{ event.id }}">hier</a></p>',
    )
    expect(plain).toBe('hier (https://example.com/{{ event.id }})')
  })

  it('preserves placeholders in link text', () => {
    const plain = htmlToPlainText(
      '<p><a href="https://example.com">{{ event.name }}</a></p>',
    )
    expect(plain).toBe('{{ event.name }} (https://example.com)')
  })

  it('preserves placeholders in plain text', () => {
    const plain = htmlToPlainText(
      '<p>Hallo {{ user.name }}, Event {{ event.name }}.</p>',
    )
    expect(plain).toBe('Hallo {{ user.name }}, Event {{ event.name }}.')
  })

  it('preserves placeholders with underscores', () => {
    const plain = htmlToPlainText('<p>{{ event_name }}</p>')
    expect(plain).toBe('{{ event_name }}')
  })

  it('converts br tags to newlines', () => {
    expect(htmlToPlainText('line1<br>line2')).toBe('line1\nline2')
  })

  it('converts list items', () => {
    const plain = htmlToPlainText('<ul><li>one</li><li>two</li></ul>')
    expect(plain).toContain('- one')
    expect(plain).toContain('- two')
  })

  it('decodes HTML entities', () => {
    expect(htmlToPlainText('&amp; &lt; &gt; &quot; &#39;')).toBe('& < > " \'')
  })
})

describe('roundtrip: markdown → HTML → markdown', () => {
  function roundtrip(md) {
    return htmlToMarkdown(markdownToHtml(md))
  }

  it('preserves a simple link', () => {
    const md = '[hier](https://example.com)'
    expect(roundtrip(md)).toContain('[hier](https://example.com)')
  })

  it('preserves a link with placeholder in URL', () => {
    const result = roundtrip(
      '[hier](https://example.com/#/events/{{ event.id }})',
    )
    expect(result).toContain(
      '[hier](https://example.com/#/events/{{ event.id }})',
    )
  })

  it('preserves a link with placeholder in text', () => {
    const result = roundtrip('[{{ event.name }}](https://example.com)')
    expect(result).toContain('[{{ event.name }}](https://example.com)')
  })

  it('preserves a link with placeholders in both URL and text', () => {
    const result = roundtrip(
      '[{{ event.name }}](https://example.com/{{ event.id }})',
    )
    expect(result).toContain('{{ event.name }}')
    expect(result).toContain('https://example.com/{{ event.id }}')
  })

  it('preserves an image with placeholder in URL', () => {
    const result = roundtrip(
      '![Alt](https://example.com/{{ event.id }}/img.png)',
    )
    expect(result).toContain('https://example.com/{{ event.id }}/img.png')
  })

  it('preserves bold text with placeholder', () => {
    const result = roundtrip('**{{ event.name }}**')
    expect(result).toContain('{{ event.name }}')
    expect(result).toMatch(/\*\*{{ event\.name }}\*\*/)
  })

  it('preserves underscore variables in text', () => {
    const result = roundtrip('Name: {{ event_name }}')
    expect(result).toContain('{{ event_name }}')
    expect(result).not.toContain('event\\_name')
  })

  it('preserves underscore variables inside bold', () => {
    const result = roundtrip('**{{ event_name }}**')
    expect(result).toContain('{{ event_name }}')
    expect(result).not.toContain('event\\_name')
  })

  it('preserves placeholder in code', () => {
    const result = roundtrip('`{{ event.id }}`')
    expect(result).toContain('{{ event.id }}')
  })

  it('preserves placeholder in heading', () => {
    const result = roundtrip('# {{ event.name }}')
    expect(result).toContain('# {{ event.name }}')
  })

  it('preserves multiple placeholders in mixed content', () => {
    const md =
      'Hallo {{ user.name }}, Details [hier](https://example.com/{{ event.id }}).'
    const result = roundtrip(md)
    expect(result).toContain('{{ user.name }}')
    expect(result).toContain('[hier](https://example.com/{{ event.id }})')
  })

  it('preserves content after multiple roundtrips', () => {
    const md =
      'Infos [hier](https://example.com/#/events/{{ event.id }}). Kontakt: {{ user.name }}.'
    const first = roundtrip(md)
    const second = roundtrip(first)
    const third = roundtrip(second)
    expect(third).toContain('https://example.com/#/events/{{ event.id }}')
    expect(third).toContain('{{ user.name }}')
    // Ensure stability after multiple conversions
    expect(third).toBe(second)
  })
})
