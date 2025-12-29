output "query_handler_arn" {
  description = "ARN of the query handler Lambda function"
  value       = aws_lambda_function.query_handler.arn
}

output "query_handler_name" {
  description = "Name of the query handler Lambda function"
  value       = aws_lambda_function.query_handler.function_name
}

output "teams_webhook_handler_arn" {
  description = "ARN of the Teams webhook handler Lambda function"
  value       = aws_lambda_function.teams_webhook_handler.arn
}

output "teams_webhook_handler_name" {
  description = "Name of the Teams webhook handler Lambda function"
  value       = aws_lambda_function.teams_webhook_handler.function_name
}

output "health_handler_arn" {
  description = "ARN of the health handler Lambda function"
  value       = aws_lambda_function.health_handler.arn
}

output "health_handler_name" {
  description = "Name of the health handler Lambda function"
  value       = aws_lambda_function.health_handler.function_name
}

output "metrics_handler_arn" {
  description = "ARN of the metrics handler Lambda function"
  value       = aws_lambda_function.metrics_handler.arn
}

output "metrics_handler_name" {
  description = "Name of the metrics handler Lambda function"
  value       = aws_lambda_function.metrics_handler.function_name
}

output "lambda_layer_arn" {
  description = "ARN of the Lambda layer with dependencies"
  value       = aws_lambda_layer_version.dependencies.arn
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

output "query_handler_invoke_arn" {
  description = "Invoke ARN of the query handler Lambda function"
  value       = aws_lambda_function.query_handler.invoke_arn
}

output "teams_webhook_handler_invoke_arn" {
  description = "Invoke ARN of the Teams webhook handler Lambda function"
  value       = aws_lambda_function.teams_webhook_handler.invoke_arn
}

output "health_handler_invoke_arn" {
  description = "Invoke ARN of the health handler Lambda function"
  value       = aws_lambda_function.health_handler.invoke_arn
}

output "metrics_handler_invoke_arn" {
  description = "Invoke ARN of the metrics handler Lambda function"
  value       = aws_lambda_function.metrics_handler.invoke_arn
}

