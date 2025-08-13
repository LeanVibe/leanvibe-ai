import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as React from 'react'
import { apiClient } from '@/lib/api-client'
import type { ListParams, Project, ProjectFile } from '@/types/api'

export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (params?: ListParams) => [...projectKeys.lists(), params] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
  files: (id: string) => [...projectKeys.detail(id), 'files'] as const,
}

export function useProjects(params?: ListParams) {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => apiClient.getProjects(params),
    staleTime: 30_000,
  })
}

export function useProject(id: string) {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => apiClient.getProject(id),
    enabled: !!id,
    staleTime: 30_000,
  })
}

export function useProjectFiles(id: string, enabled = true) {
  return useQuery<ProjectFile[]>({
    queryKey: projectKeys.files(id),
    queryFn: async () => {
      const res = await apiClient.getProjectFiles(id)
      return (res as any).data ?? res
    },
    enabled: !!id && enabled,
    refetchInterval: 10_000,
  })
}

export function useDirectoryEntries(id: string, opts?: { path?: string; sort?: 'name' | 'size' | 'modified' }) {
  const { path, sort } = opts || {}
  return useQuery<any[]>({
    queryKey: [...projectKeys.files(id), 'dir', path || '', sort || 'name'],
    queryFn: () => apiClient.getProjectDirectory(id, { path, sort }),
    enabled: !!id,
    staleTime: 10_000,
  })
}

export function useDownloadArchive() {
  return useMutation({
    mutationFn: async (id: string) => {
      const blob = await apiClient.downloadProjectArchive(id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `project_${id}.zip`
      document.body.appendChild(a)
      a.click()
      URL.revokeObjectURL(url)
      a.remove()
    },
  })
}

export async function downloadProjectFile(id: string, path: string) {
  const blob = await apiClient.downloadProjectFile(id, path)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = path.split('/').pop() || 'file'
  document.body.appendChild(a)
  a.click()
  URL.revokeObjectURL(url)
  a.remove()
}
