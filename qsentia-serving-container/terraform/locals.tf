locals {
  name = "${var.project_name}-${var.environment}"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  is_gpu_mode     = var.launch_mode == "gpu_ec2"
  container_image = var.container_image != "" ? var.container_image : "${aws_ecr_repository.serving.repository_url}:latest"
  model_s3_uri    = "s3://${aws_s3_bucket.model_artifacts.bucket}/${var.model_artifact_prefix}"
}

