# LeanVibe Enterprise Terraform Variables
# Configuration variables for multi-cloud infrastructure deployment

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "aws_region" {
  description = "AWS region for primary deployment"
  type        = string
  default     = "us-east-1"
}

variable "azure_region" {
  description = "Azure region for multi-cloud deployment"
  type        = string
  default     = "East US"
}

variable "gcp_region" {
  description = "GCP region for multi-cloud deployment"
  type        = string
  default     = "us-east1"
}

# Networking Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24", "10.0.30.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.100.0/24", "10.0.200.0/24", "10.0.300.0/24"]
}

# Kubernetes Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "cluster_endpoint_private_access" {
  description = "Enable private API server endpoint"
  type        = bool
  default     = true
}

variable "cluster_endpoint_public_access" {
  description = "Enable public API server endpoint"
  type        = bool
  default     = true
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "CIDR blocks that can access the public API server endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict this in production
}

# Database Configuration
variable "db_instance_class" {
  description = "RDS instance class for PostgreSQL"
  type        = string
  default     = "db.r5.large"

  validation {
    condition     = can(regex("^db\\.", var.db_instance_class))
    error_message = "Database instance class must start with 'db.'."
  }
}

variable "db_allocated_storage" {
  description = "Initial allocated storage for RDS (GB)"
  type        = number
  default     = 100

  validation {
    condition     = var.db_allocated_storage >= 20
    error_message = "Database allocated storage must be at least 20 GB."
  }
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS autoscaling (GB)"
  type        = number
  default     = 1000
}

variable "db_backup_retention_days" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 30

  validation {
    condition     = var.db_backup_retention_days >= 1 && var.db_backup_retention_days <= 35
    error_message = "Backup retention must be between 1 and 35 days."
  }
}

# Redis Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "redis_num_cache_clusters" {
  description = "Number of cache clusters for Redis"
  type        = number
  default     = 2
}

variable "redis_parameter_group_name" {
  description = "Parameter group name for Redis"
  type        = string
  default     = "default.redis7"
}

# Domain and SSL Configuration
variable "domain_name" {
  description = "Primary domain name for the application"
  type        = string
  default     = "leanvibe.ai"
}

variable "subdomain_names" {
  description = "List of subdomain names"
  type        = list(string)
  default     = ["api", "admin", "monitoring", "*.tenant"]
}

variable "enable_certificate_transparency_logging" {
  description = "Enable certificate transparency logging"
  type        = bool
  default     = true
}

# Multi-Cloud Configuration
variable "enable_multi_cloud" {
  description = "Enable multi-cloud deployment (AWS + Azure + GCP)"
  type        = bool
  default     = false
}

variable "primary_cloud_provider" {
  description = "Primary cloud provider (aws, azure, gcp)"
  type        = string
  default     = "aws"

  validation {
    condition     = contains(["aws", "azure", "gcp"], var.primary_cloud_provider)
    error_message = "Primary cloud provider must be one of: aws, azure, gcp."
  }
}

# Disaster Recovery Configuration
variable "enable_cross_region_backup" {
  description = "Enable cross-region backup and replication"
  type        = bool
  default     = true
}

variable "backup_regions" {
  description = "List of regions for backup replication"
  type        = list(string)
  default     = ["us-west-2", "eu-west-1"]
}

variable "rpo_minutes" {
  description = "Recovery Point Objective in minutes"
  type        = number
  default     = 5

  validation {
    condition     = var.rpo_minutes >= 1
    error_message = "RPO must be at least 1 minute."
  }
}

variable "rto_minutes" {
  description = "Recovery Time Objective in minutes"
  type        = number
  default     = 60

  validation {
    condition     = var.rto_minutes >= 1
    error_message = "RTO must be at least 1 minute."
  }
}

# Enterprise Feature Configuration
variable "enable_enterprise_features" {
  description = "Enable enterprise security and compliance features"
  type        = bool
  default     = true
}

variable "enable_sso_integration" {
  description = "Enable SSO integration (SAML, OIDC)"
  type        = bool
  default     = true
}

variable "enable_audit_logging" {
  description = "Enable comprehensive audit logging"
  type        = bool
  default     = true
}

variable "enable_compliance_monitoring" {
  description = "Enable SOC2, GDPR, HIPAA compliance monitoring"
  type        = bool
  default     = true
}

# Cost Optimization Configuration
variable "enable_cost_optimization" {
  description = "Enable cost optimization features (spot instances, auto-scaling, etc.)"
  type        = bool
  default     = true
}

variable "enable_reserved_instances" {
  description = "Use reserved instances for predictable workloads"
  type        = bool
  default     = false # Set to true after workload analysis
}

variable "auto_scaling_target_cpu" {
  description = "Target CPU utilization for auto-scaling"
  type        = number
  default     = 70

  validation {
    condition     = var.auto_scaling_target_cpu > 0 && var.auto_scaling_target_cpu <= 100
    error_message = "Auto-scaling target CPU must be between 1 and 100."
  }
}

variable "auto_scaling_target_memory" {
  description = "Target memory utilization for auto-scaling"
  type        = number
  default     = 80

  validation {
    condition     = var.auto_scaling_target_memory > 0 && var.auto_scaling_target_memory <= 100
    error_message = "Auto-scaling target memory must be between 1 and 100."
  }
}

# Monitoring and Alerting Configuration
variable "alert_email_addresses" {
  description = "List of email addresses for critical alerts"
  type        = list(string)
  default     = ["devops@leanvibe.ai", "alerts@leanvibe.ai"]

  validation {
    condition     = length(var.alert_email_addresses) > 0
    error_message = "At least one alert email address is required."
  }
}

variable "alert_slack_webhook" {
  description = "Slack webhook URL for alert notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_business_metrics" {
  description = "Enable business metrics collection (MRR, user activity, etc.)"
  type        = bool
  default     = true
}

variable "metrics_retention_days" {
  description = "Number of days to retain metrics data"
  type        = number
  default     = 90

  validation {
    condition     = var.metrics_retention_days >= 30
    error_message = "Metrics retention must be at least 30 days for enterprise compliance."
  }
}

# Security Configuration
variable "enable_waf" {
  description = "Enable Web Application Firewall"
  type        = bool
  default     = true
}

variable "enable_ddos_protection" {
  description = "Enable DDoS protection (AWS Shield Advanced)"
  type        = bool
  default     = false # Expensive, enable based on threat assessment
}

variable "enable_secrets_rotation" {
  description = "Enable automatic secrets rotation"
  type        = bool
  default     = true
}

variable "secrets_rotation_days" {
  description = "Number of days between automatic secrets rotation"
  type        = number
  default     = 90

  validation {
    condition     = var.secrets_rotation_days >= 30
    error_message = "Secrets rotation interval must be at least 30 days."
  }
}

# Network Security
variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict in production
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC flow logs for network monitoring"
  type        = bool
  default     = true
}

variable "enable_network_acls" {
  description = "Enable network ACLs for additional security"
  type        = bool
  default     = true
}

# Backup and Archive Configuration
variable "backup_schedule_cron" {
  description = "Cron expression for backup schedule"
  type        = string
  default     = "0 2 * * *" # Daily at 2 AM UTC
}

variable "long_term_backup_retention_days" {
  description = "Long-term backup retention for compliance"
  type        = number
  default     = 2555 # 7 years for financial compliance
}

variable "enable_backup_encryption" {
  description = "Enable backup encryption using KMS"
  type        = bool
  default     = true
}

# Tenant Configuration
variable "default_tenant_tier" {
  description = "Default tier for new tenants"
  type        = string
  default     = "team"

  validation {
    condition     = contains(["developer", "team", "enterprise"], var.default_tenant_tier)
    error_message = "Default tenant tier must be one of: developer, team, enterprise."
  }
}

variable "max_tenants_per_cluster" {
  description = "Maximum number of tenants per Kubernetes cluster"
  type        = number
  default     = 1000
}

variable "tenant_isolation_mode" {
  description = "Tenant isolation mode (namespace, cluster, hybrid)"
  type        = string
  default     = "namespace"

  validation {
    condition     = contains(["namespace", "cluster", "hybrid"], var.tenant_isolation_mode)
    error_message = "Tenant isolation mode must be one of: namespace, cluster, hybrid."
  }
}

# Performance Configuration
variable "enable_performance_monitoring" {
  description = "Enable detailed performance monitoring"
  type        = bool
  default     = true
}

variable "performance_budget_response_time_ms" {
  description = "Performance budget for API response time (milliseconds)"
  type        = number
  default     = 200
}

variable "performance_budget_throughput_rps" {
  description = "Performance budget for API throughput (requests per second)"
  type        = number
  default     = 1000
}

# Development and Testing
variable "enable_debug_logging" {
  description = "Enable debug-level logging (not for production)"
  type        = bool
  default     = false
}

variable "enable_test_endpoints" {
  description = "Enable test endpoints for integration testing"
  type        = bool
  default     = false
}

variable "maintenance_window" {
  description = "Preferred maintenance window (e.g., 'sun:03:00-sun:04:00')"
  type        = string
  default     = "sun:03:00-sun:04:00"
}