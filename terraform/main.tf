terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ─────────── Identidade ───────────
data "aws_caller_identity" "current" {}

# ─────────── VPC & Subnets padrão ───────────
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

# ─────────── SG já existente (somente lookup) ───────────
data "aws_security_group" "app_sg" {
  filter {
    name   = "group-name"
    values = ["order-service-sg"]
  }
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ─────────── ECR já existente (lookup) ───────────
data "aws_ecr_repository" "order_service" {
  name = var.repository_name   # "order-service-repo"
}

locals {
  image_uri = "${data.aws_ecr_repository.order_service.repository_url}:latest"
}

# ─────────── Exec-role pré-criada ───────────
data "aws_iam_role" "ecs_execution" {
  name = "LabRole"
}

# ─────────── Log group já criado (lookup) ───────────
data "aws_cloudwatch_log_group" "order_logs" {
  name = "/ecs/order-service"
}

# ─────────── ECS Cluster (Terraform gerencia) ───────────
resource "aws_ecs_cluster" "order_service_cluster" {
  name = var.cluster_name      # "order-service-cluster"
}

# ─────────── Task definition ───────────
resource "aws_ecs_task_definition" "order_service" {
  family                   = "order-service"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = data.aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name  = "order-service"
      image = local.image_uri
      essential = true
      portMappings = [{ containerPort = 80, protocol = "tcp" }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = data.aws_cloudwatch_log_group.order_logs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      # se a LabRole já tiver acesso ao segredo, mantenha;
      # senão converta para environment vars.
      secrets = [
        { name = "DB_HOST", valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:order-service-db:DB_HOST::" },
        { name = "DB_PORT", valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:order-service-db:DB_PORT::" },
        { name = "DB_NAME", valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:order-service-db:DB_NAME::" },
        { name = "DB_USER", valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:order-service-db:DB_USER::" },
        { name = "DB_PASS", valueFrom = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:order-service-db:DB_PASS::" }
      ]
    }
  ])
}

# ─────────── Service ───────────
data "aws_ecs_service" "existing_service" {
  cluster_arn  = aws_ecs_cluster.order_service_cluster.arn
  service_name = "order-service"
}

resource "aws_ecs_service" "order_service" {
  count           = length(data.aws_ecs_service.existing_service) == 0 ? 1 : 0
  name             = "order-service"
  cluster          = aws_ecs_cluster.order_service_cluster.id
  task_definition  = aws_ecs_task_definition.order_service.arn
  desired_count    = 1
  launch_type      = "FARGATE"

  network_configuration {
    subnets         = data.aws_subnets.public.ids
    security_groups = [data.aws_security_group.app_sg.id]
    assign_public_ip = true
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}

# ─────────── Outputs ───────────
output "ecr_repository_url" {
  value = data.aws_ecr_repository.order_service.repository_url
}
