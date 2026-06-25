resource "aws_cloudwatch_log_group" "serving" {
  name              = "/ecs/${local.name}"
  retention_in_days = var.log_retention_days
}

resource "aws_ecs_cluster" "serving" {
  name = local.name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

data "aws_ssm_parameter" "ecs_gpu_ami" {
  count = local.is_gpu_mode ? 1 : 0

  name = "/aws/service/ecs/optimized-ami/amazon-linux-2/gpu/recommended/image_id"
}

resource "aws_launch_template" "gpu" {
  count = local.is_gpu_mode ? 1 : 0

  name_prefix   = "${local.name}-gpu-"
  image_id      = data.aws_ssm_parameter.ecs_gpu_ami[0].value
  instance_type = var.gpu_instance_types[0]

  iam_instance_profile {
    name = aws_iam_instance_profile.gpu_instance[0].name
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.gpu_instances[0].id]
  }

  user_data = base64encode(<<-USERDATA
    #!/bin/bash
    echo ECS_CLUSTER=${aws_ecs_cluster.serving.name} >> /etc/ecs/ecs.config
  USERDATA
  )

  tag_specifications {
    resource_type = "instance"

    tags = {
      Name = "${local.name}-gpu"
    }
  }
}

resource "aws_autoscaling_group" "gpu" {
  count = local.is_gpu_mode ? 1 : 0

  name                = "${local.name}-gpu"
  min_size            = var.gpu_min_size
  max_size            = var.gpu_max_size
  desired_capacity    = var.gpu_desired_capacity
  vpc_zone_identifier = aws_subnet.private[*].id

  launch_template {
    id      = aws_launch_template.gpu[0].id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${local.name}-gpu"
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_ecs_capacity_provider" "gpu" {
  count = local.is_gpu_mode ? 1 : 0

  name = "${local.name}-gpu"

  auto_scaling_group_provider {
    auto_scaling_group_arn         = aws_autoscaling_group.gpu[0].arn
    managed_termination_protection = "DISABLED"

    managed_scaling {
      status                    = "ENABLED"
      target_capacity           = 100
      minimum_scaling_step_size = 1
      maximum_scaling_step_size = 1
    }
  }
}

resource "aws_ecs_cluster_capacity_providers" "serving" {
  count = local.is_gpu_mode ? 1 : 0

  cluster_name       = aws_ecs_cluster.serving.name
  capacity_providers = [aws_ecs_capacity_provider.gpu[0].name]

  default_capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.gpu[0].name
    weight            = 1
  }
}

resource "aws_ecs_task_definition" "serving" {
  family                   = local.name
  network_mode             = "awsvpc"
  requires_compatibilities = local.is_gpu_mode ? ["EC2"] : ["FARGATE"]
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "serving"
      image     = local.container_image
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "MODEL_BUNDLE_PATH"
          value = local.model_s3_uri
        },
        {
          name  = "MODEL_ARTIFACT_BUCKET"
          value = aws_s3_bucket.model_artifacts.bucket
        },
        {
          name  = "MODEL_ARTIFACT_PREFIX"
          value = var.model_artifact_prefix
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.serving.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "serving"
        }
      }
      resourceRequirements = local.is_gpu_mode ? [
        {
          type  = "GPU"
          value = "1"
        }
      ] : []
    }
  ])
}

resource "aws_ecs_service" "serving" {
  name            = local.name
  cluster         = aws_ecs_cluster.serving.id
  task_definition = aws_ecs_task_definition.serving.arn
  desired_count   = var.desired_count

  launch_type = local.is_gpu_mode ? null : "FARGATE"

  dynamic "capacity_provider_strategy" {
    for_each = local.is_gpu_mode ? [aws_ecs_capacity_provider.gpu[0].name] : []

    content {
      capacity_provider = capacity_provider_strategy.value
      weight            = 1
    }
  }

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.serving.arn
    container_name   = "serving"
    container_port   = var.container_port
  }

  depends_on = [
    aws_ecs_cluster_capacity_providers.serving,
    aws_lb_listener.http
  ]
}
