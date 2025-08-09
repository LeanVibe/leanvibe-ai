# LeanVibe Enterprise Terraform Outputs
# Infrastructure outputs for application configuration and monitoring

# Network Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.networking.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = module.networking.database_subnet_ids
}

output "nat_gateway_ips" {
  description = "Elastic IPs of the NAT Gateways"
  value       = module.networking.nat_gateway_ips
}

# Kubernetes Outputs
output "cluster_id" {
  description = "ID of the EKS cluster"
  value       = module.kubernetes.cluster_id
}

output "cluster_arn" {
  description = "ARN of the EKS cluster"
  value       = module.kubernetes.cluster_arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.kubernetes.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.kubernetes.cluster_security_group_id
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.kubernetes.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = module.kubernetes.cluster_oidc_issuer_url
}

output "node_groups" {
  description = "EKS node groups information"
  value       = module.kubernetes.node_groups
}

# Database Outputs
output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = module.database.db_instance_endpoint
  sensitive   = true
}

output "database_port" {
  description = "RDS instance port"
  value       = module.database.db_instance_port
}

output "database_name" {
  description = "RDS database name"
  value       = module.database.db_instance_name
}

output "database_username" {
  description = "RDS master username"
  value       = module.database.db_instance_username
  sensitive   = true
}

output "database_connection_string" {
  description = "Database connection string for applications"
  value       = "postgresql://${module.database.db_instance_username}:${random_password.neo4j_password.result}@${module.database.db_instance_endpoint}:${module.database.db_instance_port}/${module.database.db_instance_name}"
  sensitive   = true
}

output "database_read_replicas" {
  description = "Database read replica endpoints"
  value       = module.database.read_replica_endpoints
  sensitive   = true
}

# Cache Outputs
output "redis_primary_endpoint" {
  description = "Redis primary endpoint"
  value       = module.cache.redis_primary_endpoint
  sensitive   = true
}

output "redis_reader_endpoint" {
  description = "Redis reader endpoint"
  value       = module.cache.redis_reader_endpoint
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = module.cache.redis_port
}

output "redis_connection_string" {
  description = "Redis connection string for applications"
  value       = "redis://:${random_password.redis_password.result}@${module.cache.redis_primary_endpoint}:${module.cache.redis_port}"
  sensitive   = true
}

# Storage Outputs
output "application_bucket_name" {
  description = "Name of the S3 bucket for application data"
  value       = module.storage.application_bucket_name
}

output "application_bucket_arn" {
  description = "ARN of the S3 bucket for application data"
  value       = module.storage.application_bucket_arn
}

output "backup_bucket_name" {
  description = "Name of the S3 bucket for backups"
  value       = module.storage.backup_bucket_name
}

output "logs_bucket_name" {
  description = "Name of the S3 bucket for logs"
  value       = module.storage.logs_bucket_name
}

output "efs_id" {
  description = "ID of the EFS file system"
  value       = module.storage.efs_id
}

output "efs_dns_name" {
  description = "DNS name of the EFS file system"
  value       = module.storage.efs_dns_name
}

# Security Outputs
output "kms_key_id" {
  description = "ID of the KMS key for encryption"
  value       = aws_kms_key.leanvibe_key.key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS key for encryption"
  value       = aws_kms_key.leanvibe_key.arn
}

output "certificate_arn" {
  description = "ARN of the SSL certificate"
  value       = module.security.certificate_arn
}

output "waf_arn" {
  description = "ARN of the WAF WebACL"
  value       = module.security.waf_arn
}

# Load Balancer Outputs
output "application_load_balancer_arn" {
  description = "ARN of the Application Load Balancer"
  value       = module.kubernetes.application_load_balancer_arn
}

output "application_load_balancer_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.kubernetes.application_load_balancer_dns_name
}

output "application_load_balancer_zone_id" {
  description = "Canonical hosted zone ID of the Application Load Balancer"
  value       = module.kubernetes.application_load_balancer_zone_id
}

# Monitoring Outputs
output "cloudwatch_log_group_names" {
  description = "Names of CloudWatch log groups"
  value       = module.monitoring.log_group_names
}

output "sns_topic_arns" {
  description = "ARNs of SNS topics for alerting"
  value       = module.monitoring.sns_topic_arns
}

output "prometheus_endpoint" {
  description = "Prometheus endpoint for metrics collection"
  value       = module.monitoring.prometheus_endpoint
}

output "grafana_endpoint" {
  description = "Grafana dashboard endpoint"
  value       = module.monitoring.grafana_endpoint
}

# DNS Outputs
output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = module.security.route53_zone_id
}

output "domain_name" {
  description = "Primary domain name"
  value       = var.domain_name
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = "https://api.${var.domain_name}"
}

output "admin_endpoint" {
  description = "Admin interface endpoint URL"
  value       = "https://admin.${var.domain_name}"
}

# Environment Information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "region" {
  description = "AWS region"
  value       = var.aws_region
}

output "availability_zones" {
  description = "Availability zones used"
  value       = data.aws_availability_zones.available.names
}

# Cost Management Outputs
output "estimated_monthly_cost" {
  description = "Estimated monthly cost in USD"
  value = {
    kubernetes_cluster = "$150-300"
    database_primary   = "$200-500"
    database_replicas  = "$100-200"
    redis_cache        = "$100-200"
    load_balancer      = "$25-50"
    storage_s3         = "$10-100"
    storage_efs        = "$30-100"
    data_transfer      = "$50-200"
    monitoring         = "$50-150"
    total_estimated    = "$715-1800"
  }
}

# Security and Compliance Outputs
output "compliance_status" {
  description = "Compliance features enabled"
  value = {
    encryption_at_rest     = true
    encryption_in_transit  = true
    audit_logging          = var.enable_audit_logging
    network_isolation      = true
    access_control         = true
    backup_encryption      = var.enable_backup_encryption
    secrets_management     = true
    vulnerability_scanning = var.enable_enterprise_features
  }
}

# Performance and SLA Outputs
output "sla_configuration" {
  description = "SLA configuration and targets"
  value = {
    target_uptime_percentage  = "99.95%"
    target_response_time_ms   = var.performance_budget_response_time_ms
    target_throughput_rps     = var.performance_budget_throughput_rps
    backup_retention_days     = var.db_backup_retention_days
    cross_region_replication  = var.enable_cross_region_backup
    multi_az_deployment       = var.environment == "production"
    auto_scaling_enabled      = true
    disaster_recovery_rpo_min = var.rpo_minutes
    disaster_recovery_rto_min = var.rto_minutes
  }
}

# Application Configuration Outputs
output "application_configuration" {
  description = "Configuration values for application deployment"
  value = {
    database_url = "postgresql://${module.database.db_instance_username}:${random_password.neo4j_password.result}@${module.database.db_instance_endpoint}:${module.database.db_instance_port}/${module.database.db_instance_name}"
    redis_url    = "redis://:${random_password.redis_password.result}@${module.cache.redis_primary_endpoint}:${module.cache.redis_port}"
    s3_bucket    = module.storage.application_bucket_name
    kms_key_id   = aws_kms_key.leanvibe_key.key_id
    region       = var.aws_region
    environment  = var.environment
  }
  sensitive = true
}

# Multi-Cloud Outputs (if enabled)
output "multi_cloud_endpoints" {
  description = "Multi-cloud deployment endpoints"
  value = var.enable_multi_cloud ? {
    aws_endpoint   = "https://api-aws.${var.domain_name}"
    azure_endpoint = "https://api-azure.${var.domain_name}"
    gcp_endpoint   = "https://api-gcp.${var.domain_name}"
  } : null
}

# Operational Outputs
output "operational_endpoints" {
  description = "Operational and management endpoints"
  value = {
    kubernetes_dashboard = "https://k8s-dashboard.${var.domain_name}"
    prometheus_ui        = "https://prometheus.${var.domain_name}"
    grafana_dashboard    = "https://grafana.${var.domain_name}"
    neo4j_browser        = "https://neo4j.${var.domain_name}"
    kibana_dashboard     = "https://kibana.${var.domain_name}"
  }
}

# Backup and Disaster Recovery Outputs
output "backup_configuration" {
  description = "Backup and disaster recovery configuration"
  value = {
    backup_bucket            = module.storage.backup_bucket_name
    backup_schedule          = var.backup_schedule_cron
    cross_region_replication = var.enable_cross_region_backup
    backup_regions           = var.backup_regions
    encryption_key_id        = aws_kms_key.leanvibe_key.key_id
    retention_days           = var.long_term_backup_retention_days
  }
}

# Network Security Outputs
output "security_configuration" {
  description = "Network security and access control configuration"
  value = {
    vpc_flow_logs_enabled = var.enable_vpc_flow_logs
    waf_enabled           = var.enable_waf
    ddos_protection       = var.enable_ddos_protection
    network_acls_enabled  = var.enable_network_acls
    ssl_certificate_arn   = module.security.certificate_arn
    security_groups       = module.networking.security_group_ids
  }
}