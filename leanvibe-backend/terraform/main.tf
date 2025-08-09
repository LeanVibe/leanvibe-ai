# LeanVibe Enterprise Infrastructure as Code
# Multi-cloud Terraform configuration for production deployment

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }

  # Remote state configuration
  backend "s3" {
    bucket         = "leanvibe-terraform-state-prod"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "leanvibe-terraform-locks"

    # Multi-region replication for disaster recovery
    versioning = true
  }
}

# Local variables for environment configuration
locals {
  environment = var.environment
  region      = var.aws_region
  project     = "leanvibe"

  common_tags = {
    Project            = local.project
    Environment        = local.environment
    ManagedBy          = "terraform"
    Owner              = "devops@leanvibe.ai"
    CostCenter         = "leanvibe-backend"
    ComplianceLevel    = "high"
    DataClassification = "confidential"
    BackupRequired     = "true"
  }

  # Multi-tenant configuration
  tenant_tiers = {
    developer  = { cpu = "250m", memory = "512Mi", storage = "10Gi", replicas = 1 }
    team       = { cpu = "500m", memory = "1Gi", storage = "50Gi", replicas = 2 }
    enterprise = { cpu = "1000m", memory = "2Gi", storage = "200Gi", replicas = 3 }
  }

  # Enterprise SLA requirements
  sla_requirements = {
    team = {
      uptime_percentage = 99.9
      response_time_ms  = 500
      rpo_minutes       = 60
      rto_minutes       = 240
    }
    enterprise = {
      uptime_percentage = 99.95
      response_time_ms  = 200
      rpo_minutes       = 5
      rto_minutes       = 60
    }
  }
}

# Random password generation for databases
resource "random_password" "neo4j_password" {
  length  = 32
  special = true
}

resource "random_password" "redis_password" {
  length  = 32
  special = true
}

# KMS Key for encryption
resource "aws_kms_key" "leanvibe_key" {
  description             = "LeanVibe encryption key for ${local.environment}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(local.common_tags, {
    Name = "${local.project}-${local.environment}-encryption-key"
    Type = "encryption"
  })
}

resource "aws_kms_alias" "leanvibe_key_alias" {
  name          = "alias/${local.project}-${local.environment}"
  target_key_id = aws_kms_key.leanvibe_key.key_id
}

# Data sources for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Networking Module
module "networking" {
  source = "./modules/networking"

  environment = local.environment
  project     = local.project
  aws_region  = var.aws_region
  common_tags = local.common_tags

  vpc_cidr = var.vpc_cidr

  # Multi-AZ configuration for high availability
  availability_zones = data.aws_availability_zones.available.names

  # Subnet configuration for enterprise architecture
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs

  # Security configuration
  enable_nat_gateway   = true
  enable_vpn_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true
  enable_flow_logs     = true

  # Enterprise security features
  enable_waf        = true
  enable_shield     = var.environment == "production"
  enable_guard_duty = var.environment == "production"
}

# Kubernetes Cluster Module
module "kubernetes" {
  source = "./modules/kubernetes"

  environment = local.environment
  project     = local.project
  common_tags = local.common_tags

  # Cluster configuration
  cluster_version = var.kubernetes_version
  cluster_name    = "${local.project}-${local.environment}"

  # Network configuration from networking module
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  public_subnet_ids  = module.networking.public_subnet_ids

  # Node group configuration for multi-tenant workloads
  node_groups = {
    system = {
      instance_types = ["t3.medium"]
      min_size       = 2
      max_size       = 4
      desired_size   = 2
      disk_size      = 50

      labels = {
        role = "system"
        tier = "system"
      }

      taints = [{
        key    = "CriticalAddonsOnly"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }

    application = {
      instance_types = ["t3.large", "t3.xlarge"]
      min_size       = 3
      max_size       = 20
      desired_size   = 5
      disk_size      = 100

      labels = {
        role = "application"
        tier = "backend"
      }
    }

    database = {
      instance_types = ["r5.large", "r5.xlarge"]
      min_size       = 2
      max_size       = 6
      desired_size   = 3
      disk_size      = 200

      labels = {
        role = "database"
        tier = "data"
      }

      taints = [{
        key    = "database"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  # Encryption configuration
  kms_key_id = aws_kms_key.leanvibe_key.arn

  # Add-ons for enterprise features
  enable_cluster_autoscaler           = true
  enable_aws_load_balancer_controller = true
  enable_cert_manager                 = true
  enable_external_dns                 = true
  enable_prometheus_operator          = true
  enable_fluentd                      = true

  depends_on = [module.networking]
}

# Database Module (Multi-cloud RDS/CloudSQL/Azure Database)
module "database" {
  source = "./modules/database"

  environment = local.environment
  project     = local.project
  common_tags = local.common_tags

  # Network configuration
  vpc_id                 = module.networking.vpc_id
  database_subnet_ids    = module.networking.database_subnet_ids
  vpc_security_group_ids = [module.networking.database_security_group_id]

  # Neo4j configuration (using PostgreSQL as primary with Neo4j in K8s)
  db_instance_class        = var.db_instance_class
  db_allocated_storage     = var.db_allocated_storage
  db_max_allocated_storage = var.db_max_allocated_storage
  db_storage_type          = "gp3"
  db_storage_encrypted     = true
  db_kms_key_id            = aws_kms_key.leanvibe_key.arn

  # Database credentials
  db_username = "leanvibe_admin"
  db_password = random_password.neo4j_password.result

  # Backup configuration for enterprise SLA
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  # Multi-AZ for high availability
  multi_az = var.environment == "production"

  # Performance monitoring
  performance_insights_enabled = true
  monitoring_interval          = 60

  # Read replicas for scaling
  create_read_replicas = var.environment == "production"
  read_replica_count   = var.environment == "production" ? 2 : 0

  depends_on = [module.networking]
}

# Redis Cache Module
module "cache" {
  source = "./modules/cache"

  environment = local.environment
  project     = local.project
  common_tags = local.common_tags

  # Network configuration
  vpc_id             = module.networking.vpc_id
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.cache_security_group_id]

  # ElastiCache configuration
  node_type            = var.redis_node_type
  num_cache_nodes      = var.environment == "production" ? 2 : 1
  parameter_group_name = "default.redis7"
  port                 = 6379

  # High availability configuration
  automatic_failover_enabled = var.environment == "production"
  multi_az_enabled           = var.environment == "production"

  # Security configuration
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_password.result

  # Backup configuration
  snapshot_retention_limit = var.environment == "production" ? 7 : 1
  snapshot_window          = "02:00-03:00"

  depends_on = [module.networking]
}

# Storage Module (S3, EFS, etc.)
module "storage" {
  source = "./modules/storage"

  environment = local.environment
  project     = local.project
  common_tags = local.common_tags

  # S3 configuration for file storage and backups
  create_application_bucket = true
  create_backup_bucket      = true
  create_logs_bucket        = true

  # Cross-region replication for disaster recovery
  enable_cross_region_replication = var.environment == "production"
  replication_regions             = ["us-west-2", "eu-west-1"]

  # Encryption configuration
  kms_key_id = aws_kms_key.leanvibe_key.arn

  # Lifecycle policies for cost optimization
  enable_lifecycle_policies = true

  # EFS for shared storage in Kubernetes
  create_efs                          = true
  efs_throughput_mode                 = "provisioned"
  efs_provisioned_throughput_in_mibps = 100

  depends_on = [module.networking]
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"

  environment = local.environment
  project     = local.project
  common_tags = local.common_tags

  # CloudWatch configuration
  create_log_groups  = true
  log_retention_days = var.environment == "production" ? 90 : 30

  # SNS topics for alerting
  create_alerting_topics = true

  # Enterprise monitoring features
  enable_xray            = true
  enable_config          = true
  enable_cloudtrail      = true
  enable_systems_manager = true

  # Custom metrics for business KPIs
  enable_business_metrics = true

  depends_on = [module.networking, module.kubernetes]
}

# Security Module
module "security" {
  source = "./modules/security"

  environment = local.environment
  project     = local.project
  common_tags = local.common_tags

  # VPC configuration for security scanning
  vpc_id = module.networking.vpc_id

  # Security services
  enable_security_hub    = var.environment == "production"
  enable_inspector       = var.environment == "production"
  enable_macie           = var.environment == "production"
  enable_secrets_manager = true

  # WAF configuration for application protection
  enable_waf_v2 = true

  # Certificate management
  domain_name = var.domain_name

  # Secrets configuration
  database_password = random_password.neo4j_password.result
  redis_password    = random_password.redis_password.result

  depends_on = [module.networking]
}