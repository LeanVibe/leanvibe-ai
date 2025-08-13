import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as React from 'react'
import { apiClient } from '@/lib/api-client'
import { 
  Pipeline, 
  CreatePipelineRequest, 
  ListParams, 
  PipelineFilters 
} from '@/types/api'

// Query keys
export const pipelineKeys = {
  all: ['pipelines'] as const,
  lists: () => [...pipelineKeys.all, 'list'] as const,
  list: (params?: ListParams & PipelineFilters) => [...pipelineKeys.lists(), params] as const,
  details: () => [...pipelineKeys.all, 'detail'] as const,
  detail: (id: string) => [...pipelineKeys.details(), id] as const,
  status: (id: string) => [...pipelineKeys.detail(id), 'status'] as const,
  logs: (id: string) => [...pipelineKeys.detail(id), 'logs'] as const,
}

// Hooks
export function usePipelines(params?: ListParams & PipelineFilters) {
  return useQuery({
    queryKey: pipelineKeys.list(params),
    queryFn: () => apiClient.getPipelines(params),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function usePipeline(id: string) {
  return useQuery({
    queryKey: pipelineKeys.detail(id),
    queryFn: () => apiClient.getPipeline(id),
    enabled: !!id,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
  })
}

export function usePipelineStatus(id: string, enabled = true) {
  return useQuery({
    queryKey: pipelineKeys.status(id),
    queryFn: () => apiClient.getPipelineStatus(id),
    enabled: !!id && enabled,
    refetchInterval: (data) => {
      // Refetch more frequently for active pipelines
      if (data && typeof data === 'object' && 'status' in data) {
        const pipeline = data as unknown as Pipeline
        if (pipeline.status === 'in_progress' || pipeline.status === 'queued') {
          return 2000 // 2 seconds
        }
      }
      return 30000 // 30 seconds for completed/failed pipelines
    },
    staleTime: 1000, // 1 second
  })
}

export function usePipelineLogs(id: string, enabled = true) {
  return useQuery({
    queryKey: pipelineKeys.logs(id),
    queryFn: () => apiClient.getPipelineLogs(id),
    enabled: !!id && enabled,
    refetchInterval: 5000, // 5 seconds
    staleTime: 1000,
  })
}

// Live SSE tail for logs
export type TailLogEvent = {
  timestamp: string | null
  level: string
  stage?: string
  message: string
}

export function useLogsTail(
  id: string,
  options?: {
    level?: string
    stage?: string
    search?: string
    paused?: boolean
  }
) {
  const [events, setEvents] = React.useState<TailLogEvent[]>([])
  const [error, setError] = React.useState<string | null>(null)
  const [isConnected, setIsConnected] = React.useState(false)
  const { level, stage, search, paused } = options || {}

  React.useEffect(() => {
    if (!id || paused) return

    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const params = new URLSearchParams()
    if (level) params.set('level_filter', level)
    if (stage) params.set('stage_filter', stage)
    if (search) params.set('search', search)

    const url = `${base}/api/v1/pipelines/${id}/logs/tail?${params.toString()}`
    const source = new EventSource(url, { withCredentials: false })
    setIsConnected(true)
    setError(null)

    source.onmessage = (evt) => {
      try {
        const data: TailLogEvent = JSON.parse(evt.data)
        setEvents((prev) => [...prev, data])
      } catch (e) {
        // ignore parse errors
      }
    }

    source.onerror = () => {
      setIsConnected(false)
      setError('Connection error')
      source.close()
    }

    return () => {
      source.close()
      setIsConnected(false)
    }
  }, [id, level, stage, search, paused])

  const api = React.useMemo(
    () => ({
      clear: () => setEvents([]),
      pause: () => {},
      resume: () => {},
    }),
    []
  )

  return { events, error, isConnected, ...api }
}

export function useCreatePipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreatePipelineRequest) => apiClient.createPipeline(data),
    onSuccess: (newPipeline) => {
      // Invalidate and refetch pipelines list
      queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() })
      
      // Add the new pipeline to the cache
      queryClient.setQueryData(
        pipelineKeys.detail(newPipeline.id),
        newPipeline
      )
    },
  })
}

export function useUpdatePipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreatePipelineRequest> }) =>
      apiClient.updatePipeline(id, data),
    onSuccess: (updatedPipeline) => {
      // Update the pipeline in the cache
      queryClient.setQueryData(
        pipelineKeys.detail(updatedPipeline.id),
        updatedPipeline
      )
      
      // Update the pipeline in any lists that might contain it
      queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() })
    },
  })
}

export function useDeletePipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.deletePipeline(id),
    onSuccess: (_, deletedId) => {
      // Remove the pipeline from the cache
      queryClient.removeQueries({ queryKey: pipelineKeys.detail(deletedId) })
      
      // Invalidate lists to remove the deleted pipeline
      queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() })
    },
  })
}

export function useStartPipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.startPipeline(id),
    onSuccess: (updatedPipeline) => {
      // Update the pipeline status
      queryClient.setQueryData(
        pipelineKeys.detail(updatedPipeline.id),
        updatedPipeline
      )
      queryClient.setQueryData(
        pipelineKeys.status(updatedPipeline.id),
        updatedPipeline
      )
      
      // Invalidate lists to update status
      queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() })
    },
  })
}

export function usePausePipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.pausePipeline(id),
    onSuccess: (updatedPipeline) => {
      queryClient.setQueryData(
        pipelineKeys.detail(updatedPipeline.id),
        updatedPipeline
      )
      queryClient.setQueryData(
        pipelineKeys.status(updatedPipeline.id),
        updatedPipeline
      )
      queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() })
    },
  })
}

export function useResumePipeline() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.resumePipeline(id),
    onSuccess: (updatedPipeline) => {
      queryClient.setQueryData(
        pipelineKeys.detail(updatedPipeline.id),
        updatedPipeline
      )
      queryClient.setQueryData(
        pipelineKeys.status(updatedPipeline.id),
        updatedPipeline
      )
      queryClient.invalidateQueries({ queryKey: pipelineKeys.lists() })
    },
  })
}