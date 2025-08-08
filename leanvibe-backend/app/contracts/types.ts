/**
 * Generated TypeScript Types from Contract Schemas
 * 
 * This file is auto-generated from OpenAPI and AsyncAPI schemas.
 * Do not edit manually - regenerate using contracts/generate.py
 */

export namespace LeanVibeAPI {

  export interface HealthResponse {
    status: "healthy" | "degraded" | "unhealthy";
    service: string;
    version: string;
    ai_ready: boolean;
    agent_framework?: string;
    sessions?: Record<string, any>;
    event_streaming?: Record<string, any>;
    error_recovery?: Record<string, any>;
    system_status?: Record<string, any>;
    llm_metrics?: Record<string, any>;
  }

  export interface MLXHealthResponse {
    status: "healthy" | "uninitialized" | "degraded";
    model: string;
    model_loaded: boolean;
    has_pretrained_weights?: boolean;
    inference_ready: boolean;
    confidence_score: number;
    last_inference_time_ms?: number;
    memory_usage_mb?: number;
    total_inferences?: number;
    service_status?: string;
    dependencies?: Record<string, any>;
    capabilities?: Record<string, any>;
    performance?: Record<string, any>;
    recommendations?: string[];
  }

  export interface ProjectListResponse {
    projects: Project[];
    total: number;
  }

  export interface Project {
    id: string;
    name: string;
    path: string;
    status: "active" | "inactive" | "archived";
    created_at: string;
    updated_at?: string;
    language?: string;
    metrics?: ProjectMetrics;
  }

  export interface ProjectMetrics {
    lines_of_code?: number;
    file_count?: number;
    complexity_score?: number;
    test_coverage?: number;
    maintainability_index?: number;
  }

  export interface TaskListResponse {
    tasks: Task[];
    total: number;
  }

  export interface Task {
    id: string;
    title: string;
    description?: string;
    status: "todo" | "in_progress" | "done" | "cancelled";
    priority?: "low" | "medium" | "high" | "urgent";
    created_at: string;
    updated_at?: string;
    assigned_to?: string;
    project_id?: string;
  }

  export interface CodeCompletionRequest {
    file_path: string // Path to the file being edited;
    cursor_position?: number // Cursor position in the file;
    intent?: "suggest" | "explain" | "refactor" | "debug" | "optimize" // Type of completion requested;
    content?: string // Optional file content;
    language?: string // Programming language (auto-detected if not provided);
  }

  export interface CodeCompletionResponse {
    status: "success" | "error";
    intent: string;
    response: string // AI-generated response;
    confidence: number // Confidence score (0.0-1.0);
    requires_review: boolean // Whether human review is recommended;
    suggestions?: string[] // Follow-up suggestions;
    context_used: ContextUsed;
    processing_time_ms: number // Processing time in milliseconds;
    explanation?: string;
    refactoring_suggestions?: string;
    debug_analysis?: string;
    optimization_suggestions?: string;
  }

  export interface ContextUsed {
    language: string;
    symbols_found?: number;
    has_context?: boolean;
    file_path?: string;
    has_symbol_context?: boolean;
    language_detected?: string;
  }

  export interface CodeCompletionErrorResponse {
    status: "error";
    error: string // Error message;
    error_code?: string // Error code for programmatic handling;
    processing_time_ms: number // Processing time in milliseconds;
  }

  export interface ErrorResponse {
    status: string;
    error: string;
    message: string;
  }

  export interface AgentMessagePayload {
    type: string;
    content: string // Natural language query for the agent;
    workspace_path?: string // Path to the workspace directory;
  }

  export interface AgentResponsePayload {
    status: "success" | "error";
    message: string // Agent response message;
    confidence: number;
    timestamp: number // Unix timestamp;
    requires_review?: boolean;
    suggestions?: string[];
  }

  export interface CodeCompletionRequestPayload {
    type: string;
    file_path: string // Path to the file being edited;
    cursor_position?: number;
    intent?: "suggest" | "explain" | "refactor" | "debug" | "optimize";
    content?: string // Optional file content;
    language?: string // Programming language;
  }

  export interface CodeCompletionResponsePayload {
    status: "success" | "error";
    type: string;
    intent: "suggest" | "explain" | "refactor" | "debug" | "optimize";
    response: string // AI-generated response;
    confidence: number;
    requires_review?: boolean;
    suggestions?: string[];
    client_id?: string;
    timestamp: number // Unix timestamp;
    explanation?: string // Present when intent is 'explain';
    refactoring_suggestions?: string // Present when intent is 'refactor';
    debug_analysis?: string // Present when intent is 'debug';
    optimization_suggestions?: string // Present when intent is 'optimize';
  }

  export interface HeartbeatPayload {
    type: string;
    timestamp?: string;
  }

  export interface HeartbeatAckPayload {
    type: string;
    timestamp: string;
  }

  export interface CommandMessagePayload {
    type: string;
    content: string // Slash command starting with '/';
    workspace_path?: string;
  }

  export interface ReconnectionSyncPayload {
    type: string;
    data: Record<string, any>;
    timestamp: string;
  }

  export interface EventNotificationPayload {
    event_id: string;
    event_type: "system_ready" | "task_created" | "task_updated" | "task_completed" | "project_created" | "project_updated" | "code_generated" | "analysis_complete" | "agent_initialized" | "connection_established";
    priority?: "low" | "medium" | "high" | "critical";
    channel?: "system" | "development" | "collaboration" | "analytics";
    timestamp: string;
    source?: string;
    data?: Record<string, any>;
    metadata?: Record<string, any>;
  }

  export interface ErrorResponsePayload {
    status: string;
    message: string // Error message;
    confidence?: number;
    timestamp: number // Unix timestamp;
    recovery_attempted?: boolean // Whether error recovery was attempted;
    error_code?: string // Error code for programmatic handling;
  }

  // WebSocket Message Types
  export type WebSocketMessage = 
    | AgentMessagePayload 
    | CodeCompletionRequestPayload 
    | HeartbeatPayload 
    | CommandMessagePayload;

  export type WebSocketResponse = 
    | AgentResponsePayload 
    | CodeCompletionResponsePayload 
    | HeartbeatAckPayload 
    | ReconnectionSyncPayload 
    | EventNotificationPayload 
    | ErrorResponsePayload;

  // API Client Configuration
  export interface ApiConfig {
    baseUrl: string;
    websocketUrl: string;
    apiKey?: string;
    timeout?: number;
  }

  // WebSocket Connection State
  export interface WebSocketState {
    connected: boolean;
    reconnecting: boolean;
    clientId: string;
    lastHeartbeat?: number;
  }

}
