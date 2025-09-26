# ------------------------------------------------------------------
# 1. AWS Provider 설정
# ------------------------------------------------------------------
provider "aws" {
  region = "ap-northeast-2" # 한국 서울 리전
}

# ------------------------------------------------------------------
# 2. S3 버킷: 프론트엔드 파일(HTML, CSS, JS) 호스팅용
# ------------------------------------------------------------------
resource "aws_s3_bucket" "frontend_bucket" {
  bucket = var.s3_bucket_name # 변수로 버킷 이름 참조

  tags = {
    Name        = "PlaylistBotFrontend"
    Environment = "Production"
  }
}

resource "aws_s3_bucket_website_configuration" "frontend_website" {
  bucket = aws_s3_bucket.frontend_bucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_policy" "allow_public_read" {
  bucket = aws_s3_bucket.frontend_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend_bucket.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend_bucket_access]
}

resource "aws_s3_bucket_public_access_block" "frontend_bucket_access" {
  bucket = aws_s3_bucket.frontend_bucket.id

  # 이 4가지 설정을 모두 false로 변경하여
  # 버킷 정책을 통해 공개적으로 접근할 수 있도록 허용합니다.
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# ------------------------------------------------------------------
# 3. EC2 인스턴스: 백엔드 애플리케이션(app.py)을 실행할 서버
# ------------------------------------------------------------------
resource "aws_instance" "app_server" {
  ami           = "ami-0c9c942bd7bf113a2" # Amazon Linux 2 AMI (서울 리전 기준)
  instance_type = "t2.micro"

  vpc_security_group_ids = [aws_security_group.app_sg.id]

  key_name = var.ec2_key_name # 변수로 키 페어 이름 참조

  user_data = <<-EOF
              #!/bin/bash
              sudo yum update -y
              sudo amazon-linux-extras install -y python3.8
              sudo amazon-linux-extras install -y nginx1
              sudo pip3 install gunicorn fastapi uvicorn python-dotenv google-generativeai pillow python-multipart
              sudo systemctl enable nginx
              sudo systemctl start nginx
              EOF

  tags = {
    Name = "PlaylistBotAppServer"
  }
}

# ------------------------------------------------------------------
# 4. 보안 그룹: EC2 인스턴스의 방화벽 규칙
# ------------------------------------------------------------------
resource "aws_security_group" "app_sg" {
  name        = "playlist-bot-sg"
  description = "Allow HTTP, HTTPS, SSH traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # SSH 접속
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # HTTP 접속
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # HTTPS 접속
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ------------------------------------------------------------------
# 5. 출력(Outputs): 생성된 리소스의 정보를 터미널에 표시
# ------------------------------------------------------------------
output "s3_bucket_endpoint" {
  description = "프론트엔드 접속 주소 (S3 버킷 웹사이트 엔드포인트)"
  value       = aws_s3_bucket_website_configuration.frontend_website.website_endpoint
}

output "ec2_public_ip" {
  description = "백엔드 서버의 공인 IP 주소"
  value       = aws_instance.app_server.public_ip
}