variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "ami_id" {
  description = "AMI ID for EC2 instances"
  type        = string
  default     = "ami-0c02fb55956c7d316" # Amazon Linux 2023
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "desired_capacity" {
  description = "Desired number of instances in ASG"
  type        = number
  default     = 2
}

variable "min_size" {
  description = "Minimum number of instances in ASG"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of instances in ASG"
  type        = number
  default     = 10
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "RDS maximum allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "mingus_admin"
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "certificate_arn" {
  description = "SSL certificate ARN for ALB"
  type        = string
  default     = ""
}

# Feature flags
variable "enable_monitoring" {
  description = "Enable monitoring stack"
  type        = bool
  default     = true
}

variable "enable_backup" {
  description = "Enable backup service"
  type        = bool
  default     = true
}

variable "enable_auto_scaling" {
  description = "Enable auto scaling"
  type        = bool
  default     = true
}

# Scaling thresholds
variable "cpu_threshold" {
  description = "CPU utilization threshold for scaling"
  type        = number
  default     = 80
}

variable "memory_threshold" {
  description = "Memory utilization threshold for scaling"
  type        = number
  default     = 85
}

# Backup settings
variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "backup_window" {
  description = "Backup window (HH:MM-HH:MM)"
  type        = string
  default     = "02:00-04:00"
}

# Monitoring settings
variable "monitoring_retention_days" {
  description = "Number of days to retain monitoring data"
  type        = number
  default     = 30
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}

# Tags
variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

# Environment-specific overrides
locals {
  # Development environment settings
  development_settings = {
    instance_type      = "t3.small"
    desired_capacity   = 1
    min_size          = 1
    max_size          = 3
    db_instance_class = "db.t3.micro"
    db_allocated_storage = 10
    redis_node_type   = "cache.t3.micro"
  }
  
  # Staging environment settings
  staging_settings = {
    instance_type      = "t3.medium"
    desired_capacity   = 2
    min_size          = 1
    max_size          = 5
    db_instance_class = "db.t3.small"
    db_allocated_storage = 20
    redis_node_type   = "cache.t3.small"
  }
  
  # Production environment settings
  production_settings = {
    instance_type      = "t3.large"
    desired_capacity   = 3
    min_size          = 2
    max_size          = 10
    db_instance_class = "db.t3.medium"
    db_allocated_storage = 50
    redis_node_type   = "cache.t3.medium"
  }
  
  # Select settings based on environment
  environment_settings = var.environment == "development" ? local.development_settings :
                        var.environment == "staging" ? local.staging_settings :
                        local.production_settings
} 