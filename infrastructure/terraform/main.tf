terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Configure backend in terraform.tfvars or via environment variables
    # bucket = "your-terraform-state-bucket"
    # key    = "multi-agent-orchestrator/terraform.tfstate"
    # region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "multi-agent-orchestrator"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Lambda Functions
module "lambda" {
  source = "./lambda"
  
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
}

# API Gateway
module "api_gateway" {
  source = "./api_gateway"
  
  project_name = var.project_name
  environment  = var.environment
  
  # Lambda function invoke ARNs
  query_handler_lambda_arn         = module.lambda.query_handler_invoke_arn
  teams_webhook_handler_lambda_arn = module.lambda.teams_webhook_handler_invoke_arn
  health_handler_lambda_arn        = module.lambda.health_handler_invoke_arn
  metrics_handler_lambda_arn       = module.lambda.metrics_handler_invoke_arn
}

