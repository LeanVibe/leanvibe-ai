import { renderHook, act } from '@testing-library/react'
import { useLogsTail } from '@/hooks/use-pipelines'

// Minimal EventSource mock
class MockEventSource {
  url: string
  withCredentials?: boolean
  onmessage: ((this: MockEventSource, ev: MessageEvent) => any) | null = null
  onerror: ((this: MockEventSource, ev: any) => any) | null = null
  constructor(url: string, init?: { withCredentials?: boolean }) {
    this.url = url
    this.withCredentials = init?.withCredentials
    setTimeout(() => {
      this.onmessage?.({ data: JSON.stringify({ timestamp: null, level: 'INFO', message: 'hello' }) } as any)
    }, 0)
  }
  close() {}
}

describe('useLogsTail', () => {
  beforeAll(() => {
    ;(global as any).EventSource = MockEventSource as any
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
  })

  it('collects SSE events', async () => {
    const { result } = renderHook(() => useLogsTail('abc'))
    await act(async () => {
      await new Promise((r) => setTimeout(r, 5))
    })
    expect(result.current.events.length).toBeGreaterThan(0)
    expect(result.current.events[0].message).toBe('hello')
  })
})
