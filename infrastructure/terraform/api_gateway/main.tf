# API Gateway REST API
resource "aws_apigatewayv2_api" "orchestrator_api" {
  name          = "${var.project_name}-api"
  description   = "Multi-Agent Orchestrator API Gateway"
  protocol_type = "HTTP"
  
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"]
    max_age      = 300
  }
  
  tags = {
    Name        = "${var.project_name}-api"
    Environment = var.environment
  }
}

# API Gateway Stage
resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = aws_apigatewayv2_api.orchestrator_api.id
  name        = var.environment
  auto_deploy = true
  
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
  
  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }
  
  tags = {
    Name        = "${var.project_name}-api-stage"
    Environment = var.environment
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${var.project_name}-api"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.project_name}-api-logs"
    Environment = var.environment
  }
}

# API Gateway Integration for Query Handler
resource "aws_apigatewayv2_integration" "query_integration" {
  api_id           = aws_apigatewayv2_api.orchestrator_api.id
  integration_type = "AWS_PROXY"
  
  integration_uri    = var.query_handler_lambda_arn
  integration_method = "POST"
  
  payload_format_version = "2.0"
}

# API Gateway Route for Query Handler
resource "aws_apigatewayv2_route" "query_route" {
  api_id    = aws_apigatewayv2_api.orchestrator_api.id
  route_key = "POST /api/v1/query"
  
  target = "integrations/${aws_apigatewayv2_integration.query_integration.id}"
}

# API Gateway Integration for Teams Webhook
resource "aws_apigatewayv2_integration" "teams_webhook_integration" {
  api_id           = aws_apigatewayv2_api.orchestrator_api.id
  integration_type = "AWS_PROXY"
  
  integration_uri    = var.teams_webhook_handler_lambda_arn
  integration_method = "POST"
  
  payload_format_version = "2.0"
}

# API Gateway Route for Teams Webhook
resource "aws_apigatewayv2_route" "teams_webhook_route" {
  api_id    = aws_apigatewayv2_api.orchestrator_api.id
  route_key = "POST /api/teams/webhook"
  
  target = "integrations/${aws_apigatewayv2_integration.teams_webhook_integration.id}"
}

# API Gateway Integration for Health Check
resource "aws_apigatewayv2_integration" "health_integration" {
  api_id           = aws_apigatewayv2_api.orchestrator_api.id
  integration_type = "AWS_PROXY"
  
  integration_uri    = var.health_handler_lambda_arn
  integration_method = "POST"
  
  payload_format_version = "2.0"
}

# API Gateway Route for Health Check
resource "aws_apigatewayv2_route" "health_route" {
  api_id    = aws_apigatewayv2_api.orchestrator_api.id
  route_key = "GET /health"
  
  target = "integrations/${aws_apigatewayv2_integration.health_integration.id}"
}

# API Gateway Integration for Metrics
resource "aws_apigatewayv2_integration" "metrics_integration" {
  api_id           = aws_apigatewayv2_api.orchestrator_api.id
  integration_type = "AWS_PROXY"
  
  integration_uri    = var.metrics_handler_lambda_arn
  integration_method = "POST"
  
  payload_format_version = "2.0"
}

# API Gateway Route for Metrics
resource "aws_apigatewayv2_route" "metrics_route" {
  api_id    = aws_apigatewayv2_api.orchestrator_api.id
  route_key = "GET /metrics"
  
  target = "integrations/${aws_apigatewayv2_integration.metrics_integration.id}"
}

# Variables for Lambda ARNs (passed from lambda module)
variable "query_handler_lambda_arn" {
  description = "ARN of the query handler Lambda function"
  type        = string
}

variable "teams_webhook_handler_lambda_arn" {
  description = "ARN of the Teams webhook handler Lambda function"
  type        = string
}

variable "health_handler_lambda_arn" {
  description = "ARN of the health handler Lambda function"
  type        = string
}

variable "metrics_handler_lambda_arn" {
  description = "ARN of the metrics handler Lambda function"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# Lambda Permissions for API Gateway (using data sources to get function names)
data "aws_lambda_function" "query_handler" {
  function_name = split(":", var.query_handler_lambda_arn)[6]
}

data "aws_lambda_function" "teams_webhook_handler" {
  function_name = split(":", var.teams_webhook_handler_lambda_arn)[6]
}

data "aws_lambda_function" "health_handler" {
  function_name = split(":", var.health_handler_lambda_arn)[6]
}

data "aws_lambda_function" "metrics_handler" {
  function_name = split(":", var.metrics_handler_lambda_arn)[6]
}

resource "aws_lambda_permission" "query_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.query_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.orchestrator_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "teams_webhook_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.teams_webhook_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.orchestrator_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "health_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.health_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.orchestrator_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "metrics_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.metrics_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.orchestrator_api.execution_arn}/*/*"
}

