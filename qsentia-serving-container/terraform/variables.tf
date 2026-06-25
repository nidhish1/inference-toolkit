variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name prefix for resources."
  type        = string
  default     = "qsentia-serving"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "availability_zone_count" {
  description = "Number of availability zones to use."
  type        = number
  default     = 2

  validation {
    condition     = var.availability_zone_count >= 2 && var.availability_zone_count <= 3
    error_message = "availability_zone_count must be 2 or 3."
  }
}

variable "enable_nat_gateway" {
  description = "Whether to create NAT gateways for private subnet egress."
  type        = bool
  default     = true
}

variable "container_port" {
  description = "Port exposed by the serving container."
  type        = number
  default     = 8080
}

variable "container_image" {
  description = "Container image to run. Defaults to this stack's ECR repository latest tag."
  type        = string
  default     = ""
}

variable "desired_count" {
  description = "Desired number of ECS serving tasks."
  type        = number
  default     = 1
}

variable "launch_mode" {
  description = "ECS launch mode. Use fargate for CPU or gpu_ec2 for GPU capacity."
  type        = string
  default     = "fargate"

  validation {
    condition     = contains(["fargate", "gpu_ec2"], var.launch_mode)
    error_message = "launch_mode must be either fargate or gpu_ec2."
  }
}

variable "task_cpu" {
  description = "ECS task CPU units."
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "ECS task memory in MiB."
  type        = number
  default     = 2048
}

variable "model_artifact_prefix" {
  description = "S3 prefix containing the model bundle."
  type        = string
  default     = "model_bundle/"
}

variable "health_check_path" {
  description = "ALB health check path."
  type        = string
  default     = "/health"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 30
}

variable "gpu_instance_types" {
  description = "EC2 instance types for GPU ECS capacity."
  type        = list(string)
  default     = ["g5.xlarge"]
}

variable "gpu_min_size" {
  description = "Minimum GPU EC2 capacity."
  type        = number
  default     = 0
}

variable "gpu_max_size" {
  description = "Maximum GPU EC2 capacity."
  type        = number
  default     = 2
}

variable "gpu_desired_capacity" {
  description = "Desired GPU EC2 capacity."
  type        = number
  default     = 1
}

variable "allowed_ingress_cidrs" {
  description = "CIDR blocks allowed to reach the public ALB."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

