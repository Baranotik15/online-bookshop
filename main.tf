terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
  region     = var.aws_region
}

variable "aws_access_key" {
  type      = string
  sensitive = true
}

variable "aws_secret_key" {
  type      = string
  sensitive = true
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t3.small"
}

variable "key_name" {
  type    = string
  default = "bookshop-key"
}

variable "bucket_name" {
  type    = string
  default = "online-bookshop-media"
  # actual bucket is named "${bucket_name}-<random suffix>" to stay globally unique
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# SSH-ключ генерируется терраформом, приватная часть сохраняется локально
resource "tls_private_key" "bookshop" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "bookshop" {
  key_name   = var.key_name
  public_key = tls_private_key.bookshop.public_key_openssh
}

resource "local_file" "private_key" {
  content         = tls_private_key.bookshop.private_key_pem
  filename        = "${path.module}/${var.key_name}.pem"
  file_permission = "0400"
}

resource "aws_security_group" "bookshop_sg" {
  name        = "bookshop-sg"
  description = "Allow SSH, HTTP, Prometheus and Grafana for online-bookshop"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Prometheus"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Grafana"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "bookshop-sg"
  }
}

# Lets the instance read/write the media bucket without AWS keys in .env
resource "aws_iam_role" "ec2_s3" {
  name = "bookshop-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "ec2_s3" {
  name = "bookshop-ec2-s3-access"
  role = aws_iam_role.ec2_s3.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
      ]
      Resource = [
        aws_s3_bucket.media.arn,
        "${aws_s3_bucket.media.arn}/*",
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_s3" {
  name = "bookshop-ec2-profile"
  role = aws_iam_role.ec2_s3.name
}

resource "aws_instance" "bookshop" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.bookshop.key_name
  vpc_security_group_ids = [aws_security_group.bookshop_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_s3.name

  user_data = <<-EOF
    #!/bin/bash
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker ubuntu
    systemctl enable docker
    systemctl start docker
    echo "${aws_s3_bucket.media.bucket}" > /home/ubuntu/.bookshop-bucket-name
    chown ubuntu:ubuntu /home/ubuntu/.bookshop-bucket-name
  EOF

  tags = {
    Name = "online-bookshop"
  }
}

# Static public IP — doesn't change on stop/start or instance replacement,
# so EC2_HOST (GitHub secret) and ALLOWED_HOSTS don't need updating each time
resource "aws_eip" "bookshop" {
  domain   = "vpc"
  instance = aws_instance.bookshop.id

  tags = {
    Name = "bookshop-eip"
  }
}

output "instance_public_ip" {
  value = aws_eip.bookshop.public_ip
}

output "instance_private_ip" {
  value = aws_instance.bookshop.private_ip
}

output "ssh_private_key_path" {
  value = local_file.private_key.filename
}

# Random suffix keeps the bucket name globally unique (S3 names are unique across ALL AWS accounts)
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 bucket for book cover media (Django reads AWS_STORAGE_BUCKET_NAME to enable it)
resource "aws_s3_bucket" "media" {
  bucket = "${var.bucket_name}-${random_id.bucket_suffix.hex}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "media" {
  bucket = aws_s3_bucket.media.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "media" {
  bucket = aws_s3_bucket.media.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.media.arn}/*"
    }]
  })

  depends_on = [aws_s3_bucket_public_access_block.media]
}

output "s3_bucket_name" {
  value = aws_s3_bucket.media.bucket
}
