# Qsentia Serving AWS Terraform

Terraform stack for running the Qsentia serving container on AWS ECS behind an
Application Load Balancer.

It creates:

```text
VPC
├── Public subnets
│   ├── NAT gateways
│   └── Application Load Balancer
└── Private subnets
    └── ECS serving tasks

S3
└── Model artifacts

ECR
└── Serving runtime image

ECS
├── CPU mode using Fargate
└── Optional GPU mode using ECS EC2 capacity

CloudWatch
└── Container logs

IAM
├── ECS execution role
└── ECS task role with restricted S3 access
```

## Usage

```bash
cd qsentia-serving-container/terraform
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

## CPU Fargate Mode

CPU mode is the default:

```hcl
launch_mode = "fargate"
```

The ECS task runs in private subnets and is reached through the public ALB.

## GPU EC2 Mode

GPU mode creates an ECS capacity provider backed by GPU EC2 instances:

```hcl
launch_mode          = "gpu_ec2"
gpu_instance_types   = ["g5.xlarge"]
gpu_desired_capacity = 1
```

The GPU task definition requests one GPU through ECS container resource
requirements.

## Image Flow

Terraform creates ECR, but it does not build or push your image. After apply:

```bash
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t qsentia-serving ../
docker tag qsentia-serving:latest <repository-url>:latest
docker push <repository-url>:latest
```

Then run:

```bash
terraform apply -var='container_image=<repository-url>:latest'
```

## Model Bundle

The ECS task receives:

```text
MODEL_BUNDLE_PATH=s3://<bucket>/<prefix>
MODEL_ARTIFACT_BUCKET=<bucket>
MODEL_ARTIFACT_PREFIX=<prefix>
```

The application currently reads local bundle paths, so production startup should
either download this S3 prefix to a local path before app start or add native S3
bundle loading to the container.

