terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Sem um backend remoto o estado se perde a cada execução do CI e o
  # Terraform cria recursos duplicados. Crie o bucket S3 antes e descomente:
  # backend "s3" {
  #   bucket = "streamify-terraform-state"
  #   key    = "streamify/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.region
}

# Criando a VPC para isolamento da rede dos microsserviços
resource "aws_vpc" "streamify_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "streamify-vpc"
  }
}

# Internet Gateway + rota: sem isso a subnet "pública" não tem acesso à internet
resource "aws_internet_gateway" "streamify_igw" {
  vpc_id = aws_vpc.streamify_vpc.id
  tags = {
    Name = "streamify-igw"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.streamify_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.streamify_igw.id
  }

  tags = {
    Name = "streamify-public-rt"
  }
}

# Subnet Pública
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.streamify_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.region}a"
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# Grupo de Segurança (Libera portas dos microsserviços e SSH)
resource "aws_security_group" "streamify_sg" {
  name        = "streamify-sg"
  description = "Allow traffic for Streamify Microservices"
  vpc_id      = aws_vpc.streamify_vpc.id

  # SSH só a partir do IP liberado em var.ssh_allowed_cidr
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  ingress {
    from_port   = 5001
    to_port     = 5003
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# AMI do Ubuntu 22.04 buscada dinamicamente (em vez de um ID fixo que expira)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Instância EC2 para Hospedar os microsserviços
resource "aws_instance" "streamify_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.streamify_sg.id]
  key_name               = var.key_name

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update -y
              sudo apt-get install -y docker.io docker-compose
              sudo systemctl start docker
              sudo systemctl enable docker
              EOF

  tags = {
    Name = "Streamify-Core-Server"
  }
}
