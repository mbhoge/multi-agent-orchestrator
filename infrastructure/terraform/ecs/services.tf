# Service Discovery
resource "aws_service_discovery_private_dns_namespace" "main" {
  name        = "${var.project_name}.local"
  description = "Service discovery namespace for ${var.project_name}"
  vpc         = aws_vpc.main.id
}

resource "aws_service_discovery_service" "aws_agent_core" {
  name = "aws-agent-core"
  
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    
    dns_records {
      ttl  = 10
      type = "A"
    }
    
    routing_policy = "MULTIVALUE"
  }
  
  health_check_grace_period_seconds = 30
}

resource "aws_service_discovery_service" "langgraph" {
  name = "langgraph"
  
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    
    dns_records {
      ttl  = 10
      type = "A"
    }
    
    routing_policy = "MULTIVALUE"
  }
  
  health_check_grace_period_seconds = 30
}

resource "aws_service_discovery_service" "snowflake_cortex" {
  name = "snowflake-cortex"
  
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.main.id
    
    dns_records {
      ttl  = 10
      type = "A"
    }
    
    routing_policy = "MULTIVALUE"
  }
  
  health_check_grace_period_seconds = 30
}

# ECS Services
resource "aws_ecs_service" "aws_agent_core" {
  name            = "${var.project_name}-${var.environment}-aws-agent-core"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main["aws_agent_core"].arn
  desired_count   = var.ecs_service_desired_count["aws_agent_core"]
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = false
  }
  
  service_registries {
    registry_arn = aws_service_discovery_service.aws_agent_core.arn
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.aws_agent_core.arn
    container_name   = "aws-agent-core"
    container_port   = 8000
  }
  
  depends_on = [
    aws_lb_listener.aws_agent_core,
    aws_iam_role_policy_attachment.ecs_task_execution
  ]
  
  tags = {
    Name = "${var.project_name}-${var.environment}-aws-agent-core-service"
  }
}

resource "aws_ecs_service" "langgraph" {
  name            = "${var.project_name}-${var.environment}-langgraph"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main["langgraph"].arn
  desired_count   = var.ecs_service_desired_count["langgraph"]
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = false
  }
  
  service_registries {
    registry_arn = aws_service_discovery_service.langgraph.arn
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution
  ]
  
  tags = {
    Name = "${var.project_name}-${var.environment}-langgraph-service"
  }
}

resource "aws_ecs_service" "snowflake_cortex" {
  name            = "${var.project_name}-${var.environment}-snowflake-cortex"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main["snowflake_cortex"].arn
  desired_count   = var.ecs_service_desired_count["snowflake_cortex"]
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = false
  }
  
  service_registries {
    registry_arn = aws_service_discovery_service.snowflake_cortex.arn
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution
  ]
  
  tags = {
    Name = "${var.project_name}-${var.environment}-snowflake-cortex-service"
  }
}

