output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_apigatewayv2_api.orchestrator_api.id
}

output "api_gateway_arn" {
  description = "ARN of the API Gateway"
  value       = aws_apigatewayv2_api.orchestrator_api.arn
}

output "api_gateway_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.orchestrator_api.api_endpoint
}

output "api_gateway_stage_url" {
  description = "API Gateway stage URL"
  value       = "${aws_apigatewayv2_api.orchestrator_api.api_endpoint}/${aws_apigatewayv2_stage.api_stage.name}"
}

output "query_endpoint" {
  description = "Query endpoint URL"
  value       = "${aws_apigatewayv2_api.orchestrator_api.api_endpoint}/${aws_apigatewayv2_stage.api_stage.name}/api/v1/query"
}

output "teams_webhook_endpoint" {
  description = "Teams webhook endpoint URL"
  value       = "${aws_apigatewayv2_api.orchestrator_api.api_endpoint}/${aws_apigatewayv2_stage.api_stage.name}/api/teams/webhook"
}

output "health_endpoint" {
  description = "Health check endpoint URL"
  value       = "${aws_apigatewayv2_api.orchestrator_api.api_endpoint}/${aws_apigatewayv2_stage.api_stage.name}/health"
}

output "metrics_endpoint" {
  description = "Metrics endpoint URL"
  value       = "${aws_apigatewayv2_api.orchestrator_api.api_endpoint}/${aws_apigatewayv2_stage.api_stage.name}/metrics"
}

