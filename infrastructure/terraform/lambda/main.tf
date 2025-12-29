# Variables
variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

# Lambda Layer for Dependencies
resource "aws_lambda_layer_version" "dependencies" {
  filename   = "${path.module}/../../lambda_layer.zip"
  layer_name = "${var.project_name}-dependencies"
  
  compatible_runtimes = ["python3.11"]
  
  source_code_hash = filebase64sha256("${path.module}/../../lambda_layer.zip")
  
  description = "Python dependencies for multi-agent orchestrator"
  
  lifecycle {
    ignore_changes = [source_code_hash]
  }
}

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name        = "${var.project_name}-lambda-role"
    Environment = var.environment
  }
}

# IAM Policy for Lambda Functions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeAgent"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:*:*:secret:${var.project_name}/*"
        ]
      }
    ]
  })
}

# CloudWatch Log Group for Query Handler
resource "aws_cloudwatch_log_group" "query_handler_logs" {
  name              = "/aws/lambda/${var.project_name}-query-handler"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.project_name}-query-handler-logs"
    Environment = var.environment
  }
}

# Lambda Function: Query Handler
resource "aws_lambda_function" "query_handler" {
  filename      = "${path.module}/../../lambda_deployments/query_handler.zip"
  function_name = "${var.project_name}-query-handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "aws_agent_core.lambda_handlers.query_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 300  # 5 minutes
  memory_size   = 512
  
  layers = [aws_lambda_layer_version.dependencies.arn]
  
  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }
  
  source_code_hash = filebase64sha256("${path.module}/../../lambda_deployments/query_handler.zip")
  
  depends_on = [
    aws_cloudwatch_log_group.query_handler_logs,
    aws_iam_role_policy.lambda_policy
  ]
  
  tags = {
    Name        = "${var.project_name}-query-handler"
    Environment = var.environment
  }
  
  lifecycle {
    ignore_changes = [source_code_hash]
  }
}

# CloudWatch Log Group for Teams Webhook Handler
resource "aws_cloudwatch_log_group" "teams_webhook_handler_logs" {
  name              = "/aws/lambda/${var.project_name}-teams-webhook-handler"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.project_name}-teams-webhook-handler-logs"
    Environment = var.environment
  }
}

# Lambda Function: Teams Webhook Handler
resource "aws_lambda_function" "teams_webhook_handler" {
  filename      = "${path.module}/../../lambda_deployments/teams_webhook_handler.zip"
  function_name = "${var.project_name}-teams-webhook-handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "aws_agent_core.lambda_handlers.teams_webhook_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30  # Teams requires response within 10 seconds, but allow buffer
  memory_size   = 512
  
  layers = [aws_lambda_layer_version.dependencies.arn]
  
  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }
  
  source_code_hash = filebase64sha256("${path.module}/../../lambda_deployments/teams_webhook_handler.zip")
  
  depends_on = [
    aws_cloudwatch_log_group.teams_webhook_handler_logs,
    aws_iam_role_policy.lambda_policy
  ]
  
  tags = {
    Name        = "${var.project_name}-teams-webhook-handler"
    Environment = var.environment
  }
  
  lifecycle {
    ignore_changes = [source_code_hash]
  }
}

# CloudWatch Log Group for Health Handler
resource "aws_cloudwatch_log_group" "health_handler_logs" {
  name              = "/aws/lambda/${var.project_name}-health-handler"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.project_name}-health-handler-logs"
    Environment = var.environment
  }
}

# Lambda Function: Health Handler
resource "aws_lambda_function" "health_handler" {
  filename      = "${path.module}/../../lambda_deployments/health_handler.zip"
  function_name = "${var.project_name}-health-handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "aws_agent_core.lambda_handlers.health_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 10
  memory_size   = 128
  
  layers = [aws_lambda_layer_version.dependencies.arn]
  
  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }
  
  source_code_hash = filebase64sha256("${path.module}/../../lambda_deployments/health_handler.zip")
  
  depends_on = [
    aws_cloudwatch_log_group.health_handler_logs,
    aws_iam_role_policy.lambda_policy
  ]
  
  tags = {
    Name        = "${var.project_name}-health-handler"
    Environment = var.environment
  }
  
  lifecycle {
    ignore_changes = [source_code_hash]
  }
}

# CloudWatch Log Group for Metrics Handler
resource "aws_cloudwatch_log_group" "metrics_handler_logs" {
  name              = "/aws/lambda/${var.project_name}-metrics-handler"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.project_name}-metrics-handler-logs"
    Environment = var.environment
  }
}

# Lambda Function: Metrics Handler
resource "aws_lambda_function" "metrics_handler" {
  filename      = "${path.module}/../../lambda_deployments/metrics_handler.zip"
  function_name = "${var.project_name}-metrics-handler"
  role          = aws_iam_role.lambda_role.arn
  handler       = "aws_agent_core.lambda_handlers.metrics_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256
  
  layers = [aws_lambda_layer_version.dependencies.arn]
  
  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }
  
  source_code_hash = filebase64sha256("${path.module}/../../lambda_deployments/metrics_handler.zip")
  
  depends_on = [
    aws_cloudwatch_log_group.metrics_handler_logs,
    aws_iam_role_policy.lambda_policy
  ]
  
  tags = {
    Name        = "${var.project_name}-metrics-handler"
    Environment = var.environment
  }
  
  lifecycle {
    ignore_changes = [source_code_hash]
  }
}

