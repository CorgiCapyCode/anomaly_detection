
### Virtual Private Networking
# VPC
resource "aws_vpc" "vpc-production" {
  cidr_block           = "10.0.0.0/16"
  instance_tenancy     = "default"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "vpc-production"
  }
}

# Private subnet 1 for the data stream
resource "aws_subnet" "private_subnet_data_stream" {
  vpc_id                  = aws_vpc.vpc-production.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "eu-central-1a"
  map_public_ip_on_launch = false
  tags = {
    Name = "private_sn_data_stream"
  }
}

# Private subnet 2 for the anomaly detection
resource "aws_subnet" "private_subnet_anomaly_detection" {
  vpc_id                  = aws_vpc.vpc-production.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "eu-central-1a"
  map_public_ip_on_launch = false
  tags = {
    Name = "private_sn_anomaly_detection"
  }
}

# Public subnet 1 for the dashboard
resource "aws_subnet" "public_subnet_dashboard" {
  vpc_id                  = aws_vpc.vpc-production.id
  cidr_block              = "10.0.3.0/24"
  availability_zone       = "eu-central-1a"
  map_public_ip_on_launch = true
  tags = {
    Name = "public_sn_dashboard"
  }
}


### IGW & NAT for communication
# Internet gateway for the dashboard
resource "aws_internet_gateway" "internet_gateway" {
  vpc_id = aws_vpc.vpc-production.id
  tags = {
    Name = "internet-gateway"
  }
}

#Elastic IP for NAT to download the containers
resource "aws_eip" "nat_eip" {
  domain = "vpc"
}

resource "aws_nat_gateway" "nat_gateway" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.public_subnet_dashboard.id

  tags = {
    Name = "nat-gateway"
  }
}

### Private and Public Route Tables

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.vpc-production.id
}

resource "aws_route_table" "private_route_table_data_stream" {
  vpc_id = aws_vpc.vpc-production.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gateway.id
  }

  tags = {
    Name = "private-route-table-data-stream"
  }
}

resource "aws_route_table_association" "private_route_table_association_data_stream" {
  subnet_id      = aws_subnet.private_subnet_data_stream.id
  route_table_id = aws_route_table.private_route_table_data_stream.id
}

resource "aws_route_table" "private_route_table_anomaly_detection" {
  vpc_id = aws_vpc.vpc-production.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gateway.id
  }

  tags = {
    Name = "private-route-table-anomaly-detection"
  }
}

resource "aws_route_table_association" "private_route_table_association_anomaly_detection" {
  subnet_id      = aws_subnet.private_subnet_anomaly_detection.id
  route_table_id = aws_route_table.private_route_table_anomaly_detection.id
}

# Route for internet access
resource "aws_route" "internet_access" {
  route_table_id         = aws_route_table.public_route_table.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.internet_gateway.id
}

resource "aws_route_table_association" "public_subnet_association" {
  subnet_id      = aws_subnet.public_subnet_dashboard.id
  route_table_id = aws_route_table.public_route_table.id
}


### Roles
# Role definitions
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Task Role for ECS
resource "aws_iam_role" "ecs_task_role" {
  name = "ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach AmazonECSTaskExecutionRolePolicy to the Execution Role
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  role       = aws_iam_role.ecs_task_execution_role.name
}


### ECS & Task Definitions
# ECS Cluster
resource "aws_ecs_cluster" "ecs_cluster" {
  name = "production-cluster"

  tags = {
    Name = "production-cluster"
  }
}

resource "aws_ecs_cluster_capacity_providers" "ecs_cluster_capacity_providers" {
  cluster_name = aws_ecs_cluster.ecs_cluster.name

  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# Task definitions - comparable with docker-compose
resource "aws_ecs_task_definition" "stream_data_task" {
  family                   = "stream-data-task"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512

  container_definitions = jsonencode([
    {
      name  = "stream-data-container"
      image = "corgicapycode/stream_data_image:latest"
      #cpu       = 256      
      #memory    = 512
      essential = true
      environment = [
        {
          name  = "DETECTION_SERVICE_URL"
          value = "http://anomaly-detection.ecs.local:5001/anomaly_detection"
        }
      ]
      portMappings = [
        {
          containerPort = 5000
          hostPort      = 5000
          protocol      = "tcp"
        }
      ]
    }
  ])

  tags = {
    Name = "stream-data-task"
  }
}

resource "aws_ecs_task_definition" "anomaly_detection_task" {
  family                   = "anomaly-detection-task"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024

  container_definitions = jsonencode([
    {
      name  = "anomaly-detection-container"
      image = "corgicapycode/anomaly_detection_image:latest"
      #cpu       = 512      
      #memory    = 1024
      essential = true
      environment = [
        {
          name  = "DASHBOARD_SERVICE_URL"
          value = "http://dashboard.ecs.local:5002/receive_data"
        }
      ]
      portMappings = [
        {
          containerPort = 5001
          hostPort      = 5001
          protocol      = "tcp"
        }
      ]
    }
  ])

  tags = {
    Name = "anomaly-detection-task"
  }
}

resource "aws_ecs_task_definition" "dashboard_task" {
  family                   = "dashboard-task"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512

  container_definitions = jsonencode([
    {
      name  = "dashboard-container"
      image = "corgicapycode/dashboard_image:latest"
      #cpu       = 256      
      #memory    = 512
      essential = true
      environment = [
        {
          name  = "FLASK_ENV"
          value = "production"
        }
      ]
      portMappings = [
        {
          containerPort = 5002
          hostPort      = 5002
          protocol      = "tcp"
        }
      ]
    }
  ])

  tags = {
    Name = "dashboard-task"
  }
}

# ECS Services
resource "aws_service_discovery_private_dns_namespace" "ecs_namespace" {
  name        = "ecs.local"
  vpc         = aws_vpc.vpc-production.id
  description = "Private namespace for ECS services"
}

resource "aws_ecs_service" "stream_data_service" {
  name            = "stream-data-service"
  cluster         = aws_ecs_cluster.ecs_cluster.id
  task_definition = aws_ecs_task_definition.stream_data_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_subnet_data_stream.id]
    security_groups  = [aws_security_group.sg.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.stream_data_service_discovery.arn
  }
}


resource "aws_ecs_service" "anomaly_detection_service" {
  name            = "anomaly-detection-service"
  cluster         = aws_ecs_cluster.ecs_cluster.id
  task_definition = aws_ecs_task_definition.anomaly_detection_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_subnet_anomaly_detection.id]
    security_groups  = [aws_security_group.sg.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.anomaly_detection_service_discovery.arn
  }
}


resource "aws_ecs_service" "dashboard_service" {
  name            = "dashboard-service"
  cluster         = aws_ecs_cluster.ecs_cluster.id
  task_definition = aws_ecs_task_definition.dashboard_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_subnet_dashboard.id]
    security_groups  = [aws_security_group.sg.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.dashboard_service_discovery.arn
  }
}

### Discovery Services
resource "aws_service_discovery_service" "stream_data_service_discovery" {
  name = "stream-data"
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ecs_namespace.id
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
}

resource "aws_service_discovery_service" "anomaly_detection_service_discovery" {
  name = "anomaly-detection"
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ecs_namespace.id
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
}

resource "aws_service_discovery_service" "dashboard_service_discovery" {
  name = "dashboard"
  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.ecs_namespace.id
    dns_records {
      ttl  = 10
      type = "A"
    }
  }
}

# Security group

resource "aws_security_group" "sg" {
  name        = "ecs-sg"
  description = "Allow traffic between ECS services"
  vpc_id      = aws_vpc.vpc-production.id

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Allow traffic on ports 5000-5002 from the same security group
resource "aws_security_group_rule" "self_ingress" {
  type                     = "ingress"
  from_port                = 5000
  to_port                  = 5002
  protocol                 = "tcp"
  security_group_id        = aws_security_group.sg.id
  source_security_group_id = aws_security_group.sg.id
}

# Allow traffic on ports 5000-5002 from anywhere (if needed)
resource "aws_security_group_rule" "cidr_ingress" {
  type              = "ingress"
  from_port         = 5000
  to_port           = 5002
  protocol          = "tcp"
  security_group_id = aws_security_group.sg.id
  cidr_blocks       = ["0.0.0.0/0"]
}


