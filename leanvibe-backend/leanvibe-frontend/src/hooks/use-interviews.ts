import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import type { FounderInterview } from '@/types/api'

export function useCreateInterview() {
  return useMutation({
    mutationFn: async (data: Partial<FounderInterview>) => {
      return apiClient.createInterview(data)
    },
  })
}

export function useSubmitInterview() {
  return useMutation({
    mutationFn: async (id: string) => apiClient.submitInterview(id),
  })
}
