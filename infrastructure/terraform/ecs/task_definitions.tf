locals {
  task_definitions = {
    aws_agent_core = {
      family                   = "${var.project_name}-${var.environment}-aws-agent-core"
      network_mode             = "awsvpc"
      requires_compatibilities = ["FARGATE"]
      cpu                      = var.container_cpu["aws_agent_core"]
      memory                   = var.container_memory["aws_agent_core"]
      execution_role_arn       = aws_iam_role.ecs_task_execution.arn
      task_role_arn            = aws_iam_role.ecs_task.arn
      container_definitions = jsonencode([{
        name  = "aws-agent-core"
        image = "${aws_ecr_repository.repos["aws-agent-core"].repository_url}:latest"
        portMappings = [{
          containerPort = 8080
          protocol      = "tcp"
        }]
        # LangGraph supervisor is invoked in-process by aws-agent-core
        environment = [
          {
            name  = "AWS_REGION"
            value = var.aws_region
          }
        ]
        logConfiguration = {
          logDriver = "awslogs"
          options = {
            "awslogs-group"         = aws_cloudwatch_log_group.aws_agent_core.name
            "awslogs-region"        = var.aws_region
            "awslogs-stream-prefix" = "ecs"
          }
        }
      }])
    }
    
    langgraph = {
      family                   = "${var.project_name}-${var.environment}-langgraph"
      network_mode             = "awsvpc"
      requires_compatibilities = ["FARGATE"]
      cpu                      = var.container_cpu["langgraph"]
      memory                   = var.container_memory["langgraph"]
      execution_role_arn       = aws_iam_role.ecs_task_execution.arn
      task_role_arn            = aws_iam_role.ecs_task.arn
      container_definitions = jsonencode([{
        name  = "langgraph"
        image = "${aws_ecr_repository.repos["langgraph"].repository_url}:latest"
        portMappings = [{
          containerPort = 8001
          protocol      = "tcp"
        }]
        environment = [
          {
            name  = "LANGFUSE_HOST"
            value = "http://langfuse:3000"
          }
        ]
        logConfiguration = {
          logDriver = "awslogs"
          options = {
            "awslogs-group"         = aws_cloudwatch_log_group.langgraph.name
            "awslogs-region"        = var.aws_region
            "awslogs-stream-prefix" = "ecs"
          }
        }
      }])
    }
    
    snowflake_cortex = {
      family                   = "${var.project_name}-${var.environment}-snowflake-cortex"
      network_mode             = "awsvpc"
      requires_compatibilities = ["FARGATE"]
      cpu                      = var.container_cpu["snowflake_cortex"]
      memory                   = var.container_memory["snowflake_cortex"]
      execution_role_arn       = aws_iam_role.ecs_task_execution.arn
      task_role_arn            = aws_iam_role.ecs_task.arn
      container_definitions = jsonencode([{
        name  = "snowflake-cortex"
        image = "${aws_ecr_repository.repos["snowflake-cortex"].repository_url}:latest"
        portMappings = [{
          containerPort = 8002
          protocol      = "tcp"
        }]
        logConfiguration = {
          logDriver = "awslogs"
          options = {
            "awslogs-group"         = aws_cloudwatch_log_group.snowflake_cortex.name
            "awslogs-region"        = var.aws_region
            "awslogs-stream-prefix" = "ecs"
          }
        }
      }])
    }
  }
}

resource "aws_ecs_task_definition" "main" {
  for_each = local.task_definitions
  
  family                   = each.value.family
  network_mode             = each.value.network_mode
  requires_compatibilities = each.value.requires_compatibilities
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = each.value.execution_role_arn
  task_role_arn            = each.value.task_role_arn
  container_definitions     = each.value.container_definitions
  
  tags = {
    Name = each.value.family
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "aws_agent_core" {
  name              = "/ecs/${var.project_name}-${var.environment}-aws-agent-core"
  retention_in_days = var.log_retention_days
  
  tags = {
    Name = "${var.project_name}-${var.environment}-aws-agent-core-logs"
  }
}

resource "aws_cloudwatch_log_group" "langgraph" {
  name              = "/ecs/${var.project_name}-${var.environment}-langgraph"
  retention_in_days = var.log_retention_days
  
  tags = {
    Name = "${var.project_name}-${var.environment}-langgraph-logs"
  }
}

resource "aws_cloudwatch_log_group" "snowflake_cortex" {
  name              = "/ecs/${var.project_name}-${var.environment}-snowflake-cortex"
  retention_in_days = var.log_retention_days
  
  tags = {
    Name = "${var.project_name}-${var.environment}-snowflake-cortex-logs"
  }
}

