# Terraform configuration for Mingus Application Infrastructure
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "mingus-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "mingus"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC and Networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"
  
  name = "mingus-vpc-${var.environment}"
  cidr = var.vpc_cidr
  
  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway = true
  single_nat_gateway = var.environment == "production" ? false : true
  
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Environment = var.environment
  }
}

# Security Groups
resource "aws_security_group" "app" {
  name_prefix = "mingus-app-${var.environment}"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port       = 5002
    to_port         = 5002
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "mingus-app-sg-${var.environment}"
  }
}

resource "aws_security_group" "alb" {
  name_prefix = "mingus-alb-${var.environment}"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "mingus-alb-sg-${var.environment}"
  }
}

resource "aws_security_group" "database" {
  name_prefix = "mingus-db-${var.environment}"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "mingus-db-sg-${var.environment}"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "mingus-redis-${var.environment}"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "mingus-redis-sg-${var.environment}"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "mingus-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  
  enable_deletion_protection = var.environment == "production"
  
  tags = {
    Name = "mingus-alb-${var.environment}"
  }
}

resource "aws_lb_target_group" "app" {
  name     = "mingus-app-tg-${var.environment}"
  port     = 5002
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  tags = {
    Name = "mingus-app-tg-${var.environment}"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# Auto Scaling Group
resource "aws_launch_template" "app" {
  name_prefix   = "mingus-app-${var.environment}"
  image_id      = var.ami_id
  instance_type = var.instance_type
  
  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.app.id]
  }
  
  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    environment = var.environment
    db_host     = aws_db_instance.main.endpoint
    redis_host  = aws_elasticache_replication_group.main.primary_endpoint_address
  }))
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "mingus-app-${var.environment}"
    }
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "mingus-asg-${var.environment}"
  desired_capacity    = var.desired_capacity
  max_size           = var.max_size
  min_size           = var.min_size
  target_group_arns  = [aws_lb_target_group.app.arn]
  vpc_zone_identifier = module.vpc.private_subnets
  
  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }
  
  tag {
    key                 = "Name"
    value              = "mingus-app-${var.environment}"
    propagate_at_launch = true
  }
}

# Auto Scaling Policies
resource "aws_autoscaling_policy" "cpu" {
  name                   = "mingus-cpu-policy-${var.environment}"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown              = 300
  autoscaling_group_name = aws_autoscaling_group.app.name
}

resource "aws_cloudwatch_metric_alarm" "cpu" {
  alarm_name          = "mingus-cpu-alarm-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  
  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app.name
  }
  
  alarm_description = "This metric monitors EC2 CPU utilization"
  alarm_actions     = [aws_autoscaling_policy.cpu.arn]
}

# RDS Database
resource "aws_db_instance" "main" {
  identifier = "mingus-db-${var.environment}"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class
  
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_encrypted     = true
  
  db_name  = "mingus_db"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = var.environment != "production"
  
  tags = {
    Name = "mingus-db-${var.environment}"
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "mingus-db-subnet-${var.environment}"
  subnet_ids = module.vpc.private_subnets
  
  tags = {
    Name = "mingus-db-subnet-${var.environment}"
  }
}

# ElastiCache Redis
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "mingus-redis-${var.environment}"
  replication_group_description = "Mingus Redis cluster"
  node_type                 = var.redis_node_type
  port                      = 6379
  parameter_group_name      = "default.redis7"
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  automatic_failover_enabled = var.environment == "production"
  num_cache_clusters         = var.environment == "production" ? 2 : 1
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Name = "mingus-redis-${var.environment}"
  }
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "mingus-redis-subnet-${var.environment}"
  subnet_ids = module.vpc.private_subnets
}

# S3 Bucket for Backups
resource "aws_s3_bucket" "backups" {
  bucket = "mingus-backups-${var.environment}-${random_string.bucket_suffix.result}"
  
  tags = {
    Name = "mingus-backups-${var.environment}"
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  bucket = aws_s3_bucket.backups.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  bucket = aws_s3_bucket.backups.id
  
  rule {
    id     = "backup_lifecycle"
    status = "Enabled"
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
    
    expiration {
      days = 365
    }
  }
}

# IAM Roles and Policies
resource "aws_iam_role" "app" {
  name = "mingus-app-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "app" {
  name = "mingus-app-profile-${var.environment}"
  role = aws_iam_role.app.name
}

resource "aws_iam_role_policy" "app" {
  name = "mingus-app-policy-${var.environment}"
  role = aws_iam_role.app.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.backups.arn,
          "${aws_s3_bucket.backups.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      }
    ]
  })
}

# Random string for bucket naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Outputs
output "alb_dns_name" {
  description = "The DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "db_endpoint" {
  description = "The connection endpoint for the database"
  value       = aws_db_instance.main.endpoint
}

output "redis_endpoint" {
  description = "The connection endpoint for Redis"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "s3_backup_bucket" {
  description = "The S3 bucket for backups"
  value       = aws_s3_bucket.backups.bucket
} 