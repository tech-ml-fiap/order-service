########################################
# 0.  Identidade da conta (já usado p/ ARNs)
########################################
data "aws_caller_identity" "current" {}

resource "aws_ecs_cluster" "order_service_cluster" {
  name = var.cluster_name
}

########################################
# 1.  Repositório ECR
########################################
resource "aws_ecr_repository" "order_service" {
  name                 = var.repository_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

locals {
  image_uri = "${aws_ecr_repository.order_service.repository_url}:latest"
}

########################################
# 2.  Exec-Role da task (+ política default)
########################################
data "aws_iam_policy_document" "ecs_task" {
  statement {
    actions   = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "order-service-exec-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task.json
}

resource "aws_iam_role_policy_attachment" "ecs_exec_policy" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

########################################
# 3.  Policy extra: acesso ao Secrets Manager
########################################
# Segredo com as variáveis do Postgres
data "aws_secretsmanager_secret" "db" {
  name = "order-service-db"
}

resource "aws_iam_role_policy" "ecs_exec_secrets" {
  role = aws_iam_role.ecs_execution.name
  policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["secretsmanager:GetSecretValue"],
      Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:order-service-db-*"
    }]
  })
}

########################################
# 4.  CloudWatch Logs
########################################
resource "aws_cloudwatch_log_group" "order_logs" {
  name              = "/ecs/order-service"
  retention_in_days = 14
}

########################################
# 5.  Task Definition (inclui variáveis do banco)
########################################
resource "aws_ecs_task_definition" "order_service" {
  family                   = "order-service"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name      = "order-service"
      image     = local.image_uri
      essential = true

      portMappings = [{
        containerPort = 80
        protocol      = "tcp"
      }]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.order_logs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      secrets = [
        { name = "DB_HOST", valueFrom = "${data.aws_secretsmanager_secret.db.arn}:DB_HOST::" },
        { name = "DB_PORT", valueFrom = "${data.aws_secretsmanager_secret.db.arn}:DB_PORT::" },
        { name = "DB_NAME", valueFrom = "${data.aws_secretsmanager_secret.db.arn}:DB_NAME::" },
        { name = "DB_USER", valueFrom = "${data.aws_secretsmanager_secret.db.arn}:DB_USER::" },
        { name = "DB_PASS", valueFrom = "${data.aws_secretsmanager_secret.db.arn}:DB_PASS::" }
      ]
    }
  ])
}

########################################
# 6.  ECS Service
########################################
resource "aws_ecs_service" "order_service" {
  name             = "order-service"
  cluster          = aws_ecs_cluster.order_service_cluster.id
  task_definition  = aws_ecs_task_definition.order_service.arn
  desired_count    = 1
  launch_type      = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets         = data.aws_subnets.public.ids
    security_groups = [aws_security_group.app_sg.id]
    assign_public_ip = true
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
