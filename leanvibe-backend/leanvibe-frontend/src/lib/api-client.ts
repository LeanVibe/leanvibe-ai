import { 
  ApiResponse, 
  ApiError, 
  LoginRequest, 
  LoginResponse, 
  RegisterRequest,
  User,
  Pipeline,
  CreatePipelineRequest,
  Project,
  FounderInterview,
  Analytics,
  Tenant,
  ListParams,
  PipelineFilters,
  ProjectFilters
} from '@/types/api'

class ApiClient {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') {
    this.baseURL = baseURL
    this.loadToken()
  }

  private loadToken() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token')
    }
  }

  setToken(token: string) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}/api/v1${endpoint}`
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    if (this.token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${this.token}`,
      }
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        const errorData: ApiError = await response.json()
        throw new Error(errorData.error.message || 'An error occurred')
      }

      return await response.json()
    } catch (error) {
      if (error instanceof Error) {
        throw error
      }
      throw new Error('Network error')
    }
  }

  // Authentication methods
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error?.message || 'Login failed')
    }

    const data = await response.json()
    this.setToken(data.access_token)
    return data
  }

  async register(data: RegisterRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error?.message || 'Registration failed')
    }

    const result = await response.json()
    this.setToken(result.access_token)
    return result
  }

  async logout(): Promise<void> {
    try {
      await this.request('/auth/logout', { method: 'POST' })
    } finally {
      this.clearToken()
    }
  }

  async refreshToken(): Promise<LoginResponse> {
    const refreshToken = typeof window !== 'undefined' 
      ? localStorage.getItem('refresh_token') 
      : null

    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await fetch(`${this.baseURL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${refreshToken}`,
      },
    })

    if (!response.ok) {
      throw new Error('Token refresh failed')
    }

    const data = await response.json()
    this.setToken(data.access_token)
    return data
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.request<User>('/auth/me')
    return response.data
  }

  // Pipeline methods
  async getPipelines(params?: ListParams & PipelineFilters): Promise<ApiResponse<Pipeline[]>> {
    const queryParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            queryParams.append(key, value.join(','))
          } else {
            queryParams.append(key, value.toString())
          }
        }
      })
    }

    return this.request<Pipeline[]>(`/pipelines?${queryParams.toString()}`)
  }

  async getPipeline(id: string): Promise<Pipeline> {
    const response = await this.request<Pipeline>(`/pipelines/${id}`)
    return response.data
  }

  async createPipeline(data: CreatePipelineRequest): Promise<Pipeline> {
    const response = await this.request<Pipeline>('/pipelines', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return response.data
  }

  async updatePipeline(id: string, data: Partial<CreatePipelineRequest>): Promise<Pipeline> {
    const response = await this.request<Pipeline>(`/pipelines/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response.data
  }

  async deletePipeline(id: string): Promise<void> {
    await this.request(`/pipelines/${id}`, { method: 'DELETE' })
  }

  async startPipeline(id: string): Promise<Pipeline> {
    const response = await this.request<Pipeline>(`/pipelines/${id}/start`, {
      method: 'POST',
    })
    return response.data
  }

  async pausePipeline(id: string): Promise<Pipeline> {
    const response = await this.request<Pipeline>(`/pipelines/${id}/pause`, {
      method: 'POST',
    })
    return response.data
  }

  async resumePipeline(id: string): Promise<Pipeline> {
    const response = await this.request<Pipeline>(`/pipelines/${id}/resume`, {
      method: 'POST',
    })
    return response.data
  }

  async getPipelineStatus(id: string): Promise<Pipeline> {
    const response = await this.request<Pipeline>(`/pipelines/${id}/status`)
    return response.data
  }

  async getPipelineLogs(id: string): Promise<string[]> {
    const response = await this.request<string[]>(`/pipelines/${id}/logs`)
    return response.data
  }

  // Project methods
  async getProjects(params?: ListParams & ProjectFilters): Promise<ApiResponse<Project[]>> {
    const queryParams = new URLSearchParams()
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            queryParams.append(key, value.join(','))
          } else {
            queryParams.append(key, value.toString())
          }
        }
      })
    }

    return this.request<Project[]>(`/projects?${queryParams.toString()}`)
  }

  async getProject(id: string): Promise<Project> {
    const response = await this.request<Project>(`/projects/${id}`)
    return response.data
  }

  async updateProject(id: string, data: Partial<Project>): Promise<Project> {
    const response = await this.request<Project>(`/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response.data
  }

  async deleteProject(id: string): Promise<void> {
    await this.request(`/projects/${id}`, { method: 'DELETE' })
  }

  async getProjectBlueprint(id: string): Promise<any> {
    const response = await this.request<any>(`/projects/${id}/blueprint`)
    return response.data
  }

  async updateProjectBlueprint(id: string, blueprint: any): Promise<any> {
    const response = await this.request<any>(`/projects/${id}/blueprint`, {
      method: 'PUT',
      body: JSON.stringify(blueprint),
    })
    return response.data
  }

  async approveProjectBlueprint(id: string): Promise<any> {
    const response = await this.request<any>(`/projects/${id}/blueprint/approve`, {
      method: 'POST',
    })
    return response.data
  }

  async getProjectFiles(id: string): Promise<any[]> {
    const response = await this.request<any[]>(`/projects/${id}/files`)
    return response.data
  }

  async getProjectDirectory(id: string, opts?: { path?: string; sort?: 'name' | 'size' | 'modified' }): Promise<any[]> {
    const params = new URLSearchParams()
    if (opts?.path) params.set('path', opts.path)
    if (opts?.sort) params.set('sort', opts.sort)
    const suffix = params.toString() ? `?${params.toString()}` : ''
    const response = await this.request<any[]>(`/projects/${id}/files:list${suffix}`)
    return (response as any).data ?? (response as any)
  }

  async downloadProjectFile(id: string, path: string): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/api/v1/projects/${id}/files/${encodeURIComponent(path)}`, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    })

    if (!response.ok) {
      throw new Error('File download failed')
    }

    return response.blob()
  }

  async previewProjectFile(id: string, path: string): Promise<{ blob: Blob; contentType: string | null }> {
    const response = await fetch(`${this.baseURL}/api/v1/projects/${id}/files/${encodeURIComponent(path)}?preview=true`, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    })
    if (!response.ok) {
      throw new Error('Preview failed')
    }
    const blob = await response.blob()
    const contentType = response.headers.get('Content-Type')
    return { blob, contentType }
  }

  async downloadProjectArchive(id: string): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/api/v1/projects/${id}/archive`, {
      headers: {
        Authorization: `Bearer ${this.token}`,
      },
    })

    if (!response.ok) {
      throw new Error('Archive download failed')
    }

    return response.blob()
  }

  // Interview methods
  async createInterview(data: Partial<FounderInterview>): Promise<FounderInterview> {
    const response = await this.request<FounderInterview>('/interviews', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return response.data
  }

  async getInterview(id: string): Promise<FounderInterview> {
    const response = await this.request<FounderInterview>(`/interviews/${id}`)
    return response.data
  }

  async updateInterview(id: string, data: Partial<FounderInterview>): Promise<FounderInterview> {
    const response = await this.request<FounderInterview>(`/interviews/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response.data
  }

  async validateInterview(id: string): Promise<{ valid: boolean; missing_fields: string[] }> {
    const response = await this.request<{ valid: boolean; missing_fields: string[] }>(`/interviews/${id}/validate`, {
      method: 'POST',
    })
    return response.data
  }

  async submitInterview(id: string): Promise<FounderInterview> {
    const response = await this.request<FounderInterview>(`/interviews/${id}/submit`, {
      method: 'POST',
    })
    return response.data
  }

  // Analytics methods
  async getAnalytics(): Promise<Analytics> {
    const response = await this.request<Analytics>('/analytics')
    return response.data
  }

  async getPipelineAnalytics(): Promise<any> {
    const response = await this.request<any>('/analytics/pipelines')
    return response.data
  }

  async getTenantAnalytics(): Promise<any> {
    const response = await this.request<any>('/analytics/tenant')
    return response.data
  }

  async getUsageMetrics(): Promise<any> {
    const response = await this.request<any>('/analytics/usage')
    return response.data
  }

  // Tenant methods
  async getTenantInfo(): Promise<Tenant> {
    const response = await this.request<Tenant>('/tenants/me/info')
    return response.data
  }

  async updateTenantInfo(data: Partial<Tenant>): Promise<Tenant> {
    const response = await this.request<Tenant>('/tenants/me/info', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response.data
  }

  async getTenantUsage(): Promise<any> {
    const response = await this.request<any>('/tenants/me/usage')
    return response.data
  }

  async checkQuota(quotaType: string, amount: number): Promise<any> {
    const response = await this.request<any>(`/tenants/me/quota-check/${quotaType}?amount=${amount}`)
    return response.data
  }

  // Health check
  async getHealth(): Promise<any> {
    const response = await this.request<any>('/health')
    return response.data
  }
}

export const apiClient = new ApiClient()
export default apiClient