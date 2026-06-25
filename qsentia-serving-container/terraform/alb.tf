resource "aws_lb" "serving" {
  name               = local.name
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = local.name
  }
}

resource "aws_lb_target_group" "serving" {
  name        = local.name
  port        = var.container_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    enabled             = true
    path                = var.health_check_path
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    matcher             = "200"
    timeout             = 5
  }

  tags = {
    Name = local.name
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.serving.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.serving.arn
  }
}

