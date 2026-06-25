data "aws_iam_policy_document" "ecs_tasks_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name               = "${local.name}-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
}

data "aws_iam_policy_document" "model_artifact_read" {
  statement {
    sid = "ListModelArtifactPrefix"
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.model_artifacts.arn
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = [var.model_artifact_prefix, "${var.model_artifact_prefix}*"]
    }
  }

  statement {
    sid = "ReadModelArtifacts"
    actions = [
      "s3:GetObject"
    ]
    resources = [
      "${aws_s3_bucket.model_artifacts.arn}/${var.model_artifact_prefix}*"
    ]
  }
}

resource "aws_iam_policy" "model_artifact_read" {
  name   = "${local.name}-model-artifact-read"
  policy = data.aws_iam_policy_document.model_artifact_read.json
}

resource "aws_iam_role_policy_attachment" "ecs_task_model_artifact_read" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.model_artifact_read.arn
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "gpu_instance" {
  count = local.is_gpu_mode ? 1 : 0

  name               = "${local.name}-gpu-instance"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_role_policy_attachment" "gpu_instance_ecs" {
  count = local.is_gpu_mode ? 1 : 0

  role       = aws_iam_role.gpu_instance[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_instance_profile" "gpu_instance" {
  count = local.is_gpu_mode ? 1 : 0

  name = "${local.name}-gpu-instance"
  role = aws_iam_role.gpu_instance[0].name
}

