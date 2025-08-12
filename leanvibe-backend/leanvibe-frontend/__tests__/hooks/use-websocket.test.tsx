import { act, renderHook } from '@testing-library/react'
import { useWebSocket } from '@/hooks/use-websocket'

describe('useWebSocket', () => {
  let originalWebSocket: any

  class MockWebSocket {
    static OPEN = 1
    static lastInstance: MockWebSocket | null = null

    readyState = 0
    onopen: (() => void) | null = null
    onclose: (() => void) | null = null
    onmessage: ((ev: { data: string }) => void) | null = null
    onerror: ((ev: any) => void) | null = null

    constructor(public url: string) {
      MockWebSocket.lastInstance = this
    }

    open() {
      this.readyState = MockWebSocket.OPEN
      this.onopen?.()
    }

    close() {
      this.readyState = 3
      this.onclose?.()
    }

    send(_: string) {}
  }

  beforeAll(() => {
    originalWebSocket = (global as any).WebSocket
    ;(global as any).WebSocket = MockWebSocket as any
  })

  afterAll(() => {
    ;(global as any).WebSocket = originalWebSocket
  })

  it('connects and updates state', () => {
    const { result } = renderHook(() => useWebSocket({ url: 'ws://test' }))

    act(() => {
      // Trigger connect (useEffect already calls it on mount)
      result.current.connect()
      // Simulate socket opening
      MockWebSocket.lastInstance?.open()
    })

    expect(result.current.isConnected).toBe(true)
    expect(result.current.isConnecting).toBe(false)
    expect(result.current.error).toBeNull()
  })
})
