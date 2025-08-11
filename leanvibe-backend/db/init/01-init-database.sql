-- LeanVibe Database Initialization Script
-- Creates the production database and necessary extensions

-- Create database (if it doesn't exist)
SELECT 'CREATE DATABASE leanvibe_production'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'leanvibe_production');

-- Connect to the leanvibe_production database
\c leanvibe_production;

-- Create necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set default privileges
GRANT USAGE ON SCHEMA public TO postgres;
GRANT USAGE ON SCHEMA auth TO postgres;
GRANT USAGE ON SCHEMA analytics TO postgres;
GRANT USAGE ON SCHEMA monitoring TO postgres;

-- Basic tables for production readiness
-- Users and authentication
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email CITEXT UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    company_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    tenant_id UUID DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- MVP Projects
CREATE TABLE IF NOT EXISTS public.mvp_projects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    project_name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'blueprint_pending',
    interview_data JSONB,
    blueprint_data JSONB,
    generated_files JSONB,
    deployment_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Pipeline Executions
CREATE TABLE IF NOT EXISTS public.pipeline_executions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    mvp_project_id UUID REFERENCES public.mvp_projects(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    current_stage VARCHAR(50) DEFAULT 'interview_received',
    status VARCHAR(50) DEFAULT 'initializing',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    current_stage_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    stages_completed JSONB DEFAULT '[]'::jsonb,
    stage_durations JSONB DEFAULT '{}'::jsonb,
    workflow_id UUID,
    blueprint_versions JSONB DEFAULT '[]'::jsonb,
    overall_progress FLOAT DEFAULT 0.0,
    current_stage_progress FLOAT DEFAULT 0.0,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Monitoring and metrics
CREATE TABLE IF NOT EXISTS monitoring.operation_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    operation_id VARCHAR(255) NOT NULL,
    operation_type VARCHAR(100) NOT NULL,
    tenant_id UUID,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50),
    duration_ms FLOAT,
    error_type VARCHAR(100),
    error_message TEXT,
    context_data JSONB DEFAULT '{}'::jsonb,
    result_data JSONB DEFAULT '{}'::jsonb,
    error_context JSONB DEFAULT '{}'::jsonb
);

-- Journey tracking
CREATE TABLE IF NOT EXISTS analytics.journey_steps (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    journey_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    tenant_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL,
    duration_ms FLOAT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    error_type VARCHAR(100),
    step_data JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON auth.users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON auth.users(created_at);

CREATE INDEX IF NOT EXISTS idx_mvp_projects_tenant_id ON public.mvp_projects(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mvp_projects_user_id ON public.mvp_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_mvp_projects_status ON public.mvp_projects(status);
CREATE INDEX IF NOT EXISTS idx_mvp_projects_created_at ON public.mvp_projects(created_at);

CREATE INDEX IF NOT EXISTS idx_pipeline_executions_mvp_project_id ON public.pipeline_executions(mvp_project_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_executions_tenant_id ON public.pipeline_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_executions_status ON public.pipeline_executions(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_executions_started_at ON public.pipeline_executions(started_at);

CREATE INDEX IF NOT EXISTS idx_operation_logs_operation_type ON monitoring.operation_logs(operation_type);
CREATE INDEX IF NOT EXISTS idx_operation_logs_tenant_id ON monitoring.operation_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_operation_logs_started_at ON monitoring.operation_logs(started_at);
CREATE INDEX IF NOT EXISTS idx_operation_logs_status ON monitoring.operation_logs(status);

CREATE INDEX IF NOT EXISTS idx_journey_steps_journey_id ON analytics.journey_steps(journey_id);
CREATE INDEX IF NOT EXISTS idx_journey_steps_tenant_id ON analytics.journey_steps(tenant_id);
CREATE INDEX IF NOT EXISTS idx_journey_steps_timestamp ON analytics.journey_steps(timestamp);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mvp_projects_updated_at BEFORE UPDATE ON public.mvp_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA monitoring TO postgres;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA auth TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analytics TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA monitoring TO postgres;

-- Create a sample admin user (for development/testing)
-- Note: In production, this should be created through the API
INSERT INTO auth.users (email, password_hash, full_name, company_name, is_verified)
VALUES (
    'admin@leanvibe.ai',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewNiS2Pz1KjU0O62', -- password: admin123
    'LeanVibe Admin',
    'LeanVibe AI',
    true
) ON CONFLICT (email) DO NOTHING;

-- Log initialization completion
INSERT INTO monitoring.operation_logs (
    operation_id, 
    operation_type, 
    status, 
    duration_ms,
    context_data
) VALUES (
    'db-init-' || extract(epoch from now()),
    'database_initialization',
    'success',
    0.0,
    '{"message": "Database initialized successfully", "timestamp": "' || now() || '"}'::jsonb
);