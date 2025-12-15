variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "multi-agent-orchestrator"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "multi-agent-orchestrator-cluster"
}

variable "ecs_service_desired_count" {
  description = "Desired number of tasks for ECS services"
  type        = map(number)
  default = {
    aws_agent_core    = 2
    langgraph        = 2
    snowflake_cortex = 3
  }
}

variable "container_cpu" {
  description = "CPU units for containers"
  type        = map(number)
  default = {
    aws_agent_core    = 1024
    langgraph        = 1024
    snowflake_cortex = 1024
  }
}

variable "container_memory" {
  description = "Memory for containers in MB"
  type        = map(number)
  default = {
    aws_agent_core    = 2048
    langgraph        = 2048
    snowflake_cortex = 2048
  }
}

variable "ecr_repositories" {
  description = "List of ECR repository names"
  type        = list(string)
  default = [
    "aws-agent-core",
    "langgraph",
    "snowflake-cortex"
  ]
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the load balancer"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enable_logging" {
  description = "Enable CloudWatch logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

