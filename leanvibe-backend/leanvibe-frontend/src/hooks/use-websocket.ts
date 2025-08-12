import { useEffect, useRef, useState, useCallback } from 'react'
import { WebSocketMessage, PipelineUpdate, Notification } from '@/types/api'

interface UseWebSocketOptions {
  url?: string
  onMessage?: (message: WebSocketMessage) => void
  onPipelineUpdate?: (update: PipelineUpdate) => void
  onNotification?: (notification: Notification) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

interface WebSocketState {
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  reconnectAttempts: number
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8765/ws',
    onMessage,
    onPipelineUpdate,
    onNotification,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
  } = options

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0
  })

  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const shouldReconnect = useRef(true)

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }))

    try {
      const token = typeof window !== 'undefined' 
        ? localStorage.getItem('access_token') 
        : null

      const wsUrl = token ? `${url}?token=${token}` : url
      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempts: 0
        }))
        onConnect?.()
      }

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          // Handle different message types
          switch (message.type) {
            case 'pipeline_update':
              onPipelineUpdate?.(message.data as PipelineUpdate)
              break
            case 'notification':
              onNotification?.(message.data as Notification)
              break
            default:
              break
          }

          onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.current.onclose = () => {
        setState(prev => ({ ...prev, isConnected: false, isConnecting: false }))
        onDisconnect?.()

        setState(currentState => {
          if (shouldReconnect.current && currentState.reconnectAttempts < maxReconnectAttempts) {
            reconnectTimeoutRef.current = setTimeout(() => {
              setState(prev => ({ ...prev, reconnectAttempts: prev.reconnectAttempts + 1 }))
              connect()
            }, reconnectInterval)
          }
          return currentState
        })
      }

      ws.current.onerror = (error) => {
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error',
          isConnecting: false
        }))
        onError?.(error)
      }

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'Failed to create WebSocket connection',
        isConnecting: false
      }))
    }
  }, [url, onMessage, onPipelineUpdate, onNotification, onConnect, onDisconnect, onError, reconnectInterval, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    shouldReconnect.current = false
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (ws.current) {
      ws.current.close()
      ws.current = null
    }

    setState({
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempts: 0
    })
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
      return true
    }
    return false
  }, [])

  const reconnect = useCallback(() => {
    if (state.reconnectAttempts < maxReconnectAttempts) {
      setState(prev => ({ ...prev, reconnectAttempts: 0 }))
      shouldReconnect.current = true
      connect()
    }
  }, [connect, maxReconnectAttempts, state.reconnectAttempts])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return {
    ...state,
    connect,
    disconnect,
    reconnect,
    sendMessage
  }
}