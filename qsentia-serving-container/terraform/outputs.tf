output "alb_dns_name" {
  description = "Public DNS name of the Application Load Balancer."
  value       = aws_lb.serving.dns_name
}

output "health_url" {
  description = "Health check URL."
  value       = "http://${aws_lb.serving.dns_name}${var.health_check_path}"
}

output "ecr_repository_url" {
  description = "ECR repository URL for the serving image."
  value       = aws_ecr_repository.serving.repository_url
}

output "model_artifact_bucket" {
  description = "S3 bucket for model artifacts."
  value       = aws_s3_bucket.model_artifacts.bucket
}

output "model_artifact_prefix" {
  description = "S3 prefix expected by the ECS task."
  value       = var.model_artifact_prefix
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.serving.name
}

output "ecs_service_name" {
  description = "ECS service name."
  value       = aws_ecs_service.serving.name
}

