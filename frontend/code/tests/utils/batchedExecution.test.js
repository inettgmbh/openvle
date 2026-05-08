import { describe, expect, it, vi } from 'vitest'

import { delay, executeBatched } from '@/utils/batchedExecution'

describe('executeBatched', () => {
  it('executes all operations', async () => {
    const operations = [
      () => Promise.resolve('a'),
      () => Promise.resolve('b'),
      () => Promise.resolve('c'),
    ]

    const { results, errors } = await executeBatched(operations)

    expect(results).toEqual(['a', 'b', 'c'])
    expect(errors).toEqual([])
  })

  it('executes operations in order', async () => {
    const order = []
    const operations = [1, 2, 3, 4, 5].map((n) => async () => {
      order.push(n)
      return n
    })

    const { results } = await executeBatched(operations, { batchSize: 2 })

    expect(results).toEqual([1, 2, 3, 4, 5])
    // All operations should complete
    expect(order.sort()).toEqual([1, 2, 3, 4, 5])
  })

  it('respects batch size', async () => {
    const callTimes = []
    const operations = [1, 2, 3, 4, 5].map((n) => () => {
      callTimes.push(Date.now())
      return Promise.resolve(n)
    })

    await executeBatched(operations, { batchSize: 2, delayMs: 50 })

    // Should have 3 batches: [1,2], [3,4], [5]
    // First two calls should be nearly simultaneous
    expect(callTimes[1] - callTimes[0]).toBeLessThan(20)
    // Third call should be after delay
    expect(callTimes[2] - callTimes[1]).toBeGreaterThanOrEqual(45)
    // Fourth call should be nearly simultaneous with third
    expect(callTimes[3] - callTimes[2]).toBeLessThan(20)
  })

  it('calls onProgress callback after each batch', async () => {
    const progressCalls = []
    const operations = [1, 2, 3, 4, 5].map((n) => () => Promise.resolve(n))

    await executeBatched(operations, {
      batchSize: 2,
      onProgress: (completed, total) => {
        progressCalls.push({ completed, total })
      },
    })

    expect(progressCalls).toEqual([
      { completed: 2, total: 5 },
      { completed: 4, total: 5 },
      { completed: 5, total: 5 },
    ])
  })

  it('collects errors without stopping execution', async () => {
    const operations = [
      () => Promise.resolve('ok'),
      () => Promise.reject(new Error('fail')),
      () => Promise.resolve('also ok'),
    ]

    const { results, errors } = await executeBatched(operations)

    expect(results[0]).toBe('ok')
    expect(results[1]).toBe(null)
    expect(results[2]).toBe('also ok')
    expect(errors.length).toBe(1)
    expect(errors[0].index).toBe(1)
    expect(errors[0].error.message).toBe('fail')
  })

  it('collects multiple errors', async () => {
    const operations = [
      () => Promise.reject(new Error('first')),
      () => Promise.resolve('ok'),
      () => Promise.reject(new Error('second')),
    ]

    const { results, errors } = await executeBatched(operations)

    expect(results).toEqual([null, 'ok', null])
    expect(errors.length).toBe(2)
    expect(errors[0].index).toBe(0)
    expect(errors[1].index).toBe(2)
  })

  it('handles empty operations array', async () => {
    const { results, errors } = await executeBatched([])

    expect(results).toEqual([])
    expect(errors).toEqual([])
  })

  it('handles single operation', async () => {
    const { results, errors } = await executeBatched([
      () => Promise.resolve('single'),
    ])

    expect(results).toEqual(['single'])
    expect(errors).toEqual([])
  })

  it('uses default options when not provided', async () => {
    const operations = [() => Promise.resolve('a')]
    const { results } = await executeBatched(operations)
    expect(results).toEqual(['a'])
  })

  it('skips delay after last batch', async () => {
    const startTime = Date.now()
    const operations = [1, 2, 3].map((n) => () => Promise.resolve(n))

    await executeBatched(operations, { batchSize: 3, delayMs: 100 })

    const elapsed = Date.now() - startTime
    // Should complete quickly since all ops are in one batch
    expect(elapsed).toBeLessThan(50)
  })
})

describe('delay', () => {
  it('delays for specified time', async () => {
    const start = Date.now()
    await delay(100)
    const elapsed = Date.now() - start

    expect(elapsed).toBeGreaterThanOrEqual(95)
    expect(elapsed).toBeLessThan(2000)
  })

  it('resolves with undefined', async () => {
    const result = await delay(10)
    expect(result).toBeUndefined()
  })
})
