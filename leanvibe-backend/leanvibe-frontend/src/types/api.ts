// Authentication types
export interface User {
  id: string
  email: string
  role: string
  tenant_id: string
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  email: string
  password: string
  provider?: 'local' | 'google' | 'microsoft'
}

export interface LoginResponse {
  success: boolean
  access_token: string
  refresh_token: string
  expires_in: number
  user: User
}

export interface RegisterRequest {
  email: string
  password: string
  organization_name?: string
}

// Pipeline types
export interface Pipeline {
  id: string
  project_name: string
  status: 'queued' | 'in_progress' | 'completed' | 'failed' | 'paused'
  progress_percentage: number
  current_step: string
  estimated_completion: string
  created_at: string
  updated_at: string
  configuration: PipelineConfiguration
  deliverables?: PipelineDeliverables
}

export interface PipelineConfiguration {
  priority: 'low' | 'medium' | 'high'
  auto_deploy: boolean
  quality_gates: {
    require_tests: boolean
    min_test_coverage: number
    security_scan: boolean
  }
}

export interface PipelineDeliverables {
  files_created: number
  tests_written: number
  api_endpoints: number
  documentation_pages: number
}

export interface CreatePipelineRequest {
  project_name: string
  founder_interview: FounderInterview
  configuration: PipelineConfiguration
}

// Interview types
export interface FounderInterview {
  id?: string
  business_idea: string
  target_audience: string
  key_features: string[]
  tech_preferences: string[]
  timeline: string
  budget_range: string
  business_model: string
  competitive_analysis: string
  success_metrics: string[]
  additional_requirements?: string
  completed_at?: string
}

export interface InterviewQuestion {
  id: string
  question: string
  type: 'text' | 'multiple_choice' | 'checkbox' | 'scale'
  required: boolean
  options?: string[]
  placeholder?: string
  validation?: {
    min_length?: number
    max_length?: number
    pattern?: string
  }
}

// Project types
export interface Project {
  id: string
  name: string
  description: string
  status: 'created' | 'in_progress' | 'completed' | 'deployed'
  tech_stack: string[]
  repository_url?: string
  deployment_url?: string
  created_at: string
  updated_at: string
  blueprint?: ProjectBlueprint
  files: ProjectFile[]
}

export interface ProjectBlueprint {
  id: string
  project_id: string
  architecture: string
  database_schema: string
  api_endpoints: BlueprintEndpoint[]
  frontend_components: string[]
  deployment_strategy: string
  approved: boolean
  version: number
  created_at: string
}

export interface BlueprintEndpoint {
  path: string
  method: string
  description: string
  parameters: any[]
  responses: any[]
}

export interface ProjectFile {
  path: string
  size: number
  type: 'file' | 'directory'
  modified_at: string
  download_url?: string
}

// Analytics types
export interface Analytics {
  pipelines: PipelineAnalytics
  projects: ProjectAnalytics
  user_engagement: UserEngagementAnalytics
  system_performance: SystemPerformanceAnalytics
}

export interface PipelineAnalytics {
  total_pipelines: number
  successful_pipelines: number
  failed_pipelines: number
  average_completion_time: number
  success_rate: number
  popular_tech_stacks: TechStackUsage[]
}

export interface ProjectAnalytics {
  total_projects: number
  deployed_projects: number
  average_project_size: number
  popular_features: FeatureUsage[]
}

export interface UserEngagementAnalytics {
  active_users: number
  session_duration: number
  feature_adoption: FeatureAdoption[]
  user_retention: number
}

export interface SystemPerformanceAnalytics {
  api_response_time: number
  uptime_percentage: number
  error_rate: number
  throughput: number
}

export interface TechStackUsage {
  technology: string
  usage_count: number
  success_rate: number
}

export interface FeatureUsage {
  feature: string
  usage_count: number
  adoption_rate: number
}

export interface FeatureAdoption {
  feature: string
  adoption_percentage: number
  growth_rate: number
}

// WebSocket types
export interface WebSocketMessage {
  type: 'pipeline_update' | 'notification' | 'system_alert'
  data: any
  timestamp: string
}

export interface PipelineUpdate {
  pipeline_id: string
  status: Pipeline['status']
  progress_percentage: number
  current_step: string
  estimated_completion: string
  message?: string
}

export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  action_url?: string
  read: boolean
  created_at: string
}

// API Response types
export interface ApiResponse<T> {
  data: T
  pagination?: {
    total_count: number
    current_page: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
  metadata: {
    request_id: string
    timestamp: string
    version: string
  }
}

export interface ApiError {
  error: {
    code: number
    message: string
    type: string
    request_id: string
    timestamp: number
    path: string
    details?: any
  }
}

// Tenant types
export interface Tenant {
  id: string
  organization_name: string
  slug: string
  status: 'active' | 'suspended' | 'trial'
  plan: 'developer' | 'team' | 'enterprise'
  data_residency: string
  quotas: TenantQuotas
  current_usage: TenantUsage
  created_at: string
  trial_ends_at?: string
}

export interface TenantQuotas {
  max_users: number
  max_projects: number
  max_api_calls_per_month: number
  max_storage_mb: number
  max_ai_requests_per_day: number
  max_concurrent_sessions: number
}

export interface TenantUsage {
  users_count: number
  projects_count: number
  api_calls_this_month: number
  storage_used_mb: number
  ai_requests_today: number
  concurrent_sessions: number
}

// Billing types
export interface BillingPlan {
  id: string
  name: string
  slug: string
  base_price: number
  currency: string
  billing_interval: 'monthly' | 'yearly'
  features: Record<string, any>
  trial_period_days: number
  is_enterprise?: boolean
}

export interface Subscription {
  id: string
  tenant_id: string
  plan_id: string
  status: 'active' | 'cancelled' | 'past_due' | 'trialing'
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
  created_at: string
}

// Query and filter types
export interface ListParams {
  limit?: number
  offset?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  filters?: Record<string, any>
}

export interface PipelineFilters {
  status?: Pipeline['status'][]
  created_after?: string
  created_before?: string
  project_name?: string
}

export interface ProjectFilters {
  status?: Project['status'][]
  tech_stack?: string[]
  created_after?: string
  created_before?: string
}