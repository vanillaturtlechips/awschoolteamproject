# ------------------------------------------------------------------
# 1. 기본 설정 (Provider, Data Source)
# ------------------------------------------------------------------
provider "aws" {
  region = var.aws_region
}

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# ------------------------------------------------------------------
# 2. 네트워킹 (VPC, Subnets, Gateways, Routing)
# ------------------------------------------------------------------
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  tags = { Name = "playlist-bot-vpc" }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags = { Name = "public-subnet-a" }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_a_cidr
  availability_zone = "${var.aws_region}a"
  tags = { Name = "private-subnet-a" }
}

resource "aws_subnet" "public_c" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_c_cidr
  availability_zone       = "${var.aws_region}c"
  map_public_ip_on_launch = true
  tags = { Name = "public-subnet-c" }
}

resource "aws_subnet" "private_c" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_c_cidr
  availability_zone = "${var.aws_region}c"
  tags = { Name = "private-subnet-c" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "main-igw" }
}

resource "aws_eip" "nat" {
  domain = "vpc"
  tags = { Name = "nat-eip" }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id
  tags = { Name = "main-nat-gateway" }
  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "public-rt" }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
  tags = { Name = "private-rt" }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}
resource "aws_route_table_association" "public_c" {
  subnet_id      = aws_subnet.public_c.id
  route_table_id = aws_route_table.public.id
}
resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private.id
}
resource "aws_route_table_association" "private_c" {
  subnet_id      = aws_subnet.private_c.id
  route_table_id = aws_route_table.private.id
}

# ------------------------------------------------------------------
# 3. 보안 그룹 (ELB용, EC2용)
# ------------------------------------------------------------------
resource "aws_security_group" "elb_sg" {
  name   = "playlist-bot-elb-sg"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "elb-sg" }
}

resource "aws_security_group" "ec2_sg" {
  name   = "playlist-bot-ec2-sg"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port       = 8000 # Gunicorn 포트
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.elb_sg.id] # ELB로부터의 트래픽만 허용
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # 외부 API 호출 등을 위해 모든 아웃바운드 허용
  }
  tags = { Name = "ec2-sg" }
}

# ------------------------------------------------------------------
# 4. 로드 밸런서 (ELB)
# ------------------------------------------------------------------
resource "aws_lb" "main" {
  name               = "playlist-bot-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.elb_sg.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_c.id]
  tags = { Name = "main-alb" }
}

resource "aws_lb_target_group" "main" {
  name     = "playlist-bot-tg"
  port     = 8000 # EC2 인스턴스에서 실행되는 Gunicorn 포트
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  health_check {
    path                = "/" # health check 경로 (필요시 변경)
    protocol            = "HTTP"
    matcher             = "200"
  }
  tags = { Name = "main-tg" }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# ------------------------------------------------------------------
# 5. Auto Scaling Group & EC2 시작 템플릿
# ------------------------------------------------------------------
resource "aws_launch_template" "main" {
  name_prefix   = "playlist-bot-lt"
  image_id      = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  key_name      = var.ec2_key_name
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]

  # --- [중요] Playlist-Bot 애플리케이션 배포 스크립트 ---
  user_data = base64encode(<<-EOF
              #!/bin/bash
              yum update -y
              yum install -y git
              amazon-linux-extras install -y python3.8

              mkdir /home/ec2-user/app
              cd /home/ec2-user/app
              # [주의!] 아래 주소는 실제 본인의 Git 리포지토리 주소로 변경해야 합니다.
              git clone https://github.com/vanillaturtlechips/awschoolteamproject.git .

              python3.8 -m venv venv
              source venv/bin/activate
              pip install -r requirements.txt

              # [주의!] 아래 YOUR_GEMINI_API_KEY, YOUR_YOUTUBE_API_KEY 부분은 실제 키 값으로 변경해야 합니다.
              echo "GEMINI_API_KEY=YOUR_GEMINI_API_KEY" > .env
              echo "YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY" >> .env

              # ELB Health Check를 위한 간단한 루트 경로 추가
              # app.py에 health check 경로가 이미 있다면 이 부분은 필요 없습니다.
              # sed -i "/app = FastAPI()/a @app.get('/')\nasync def health_check():\n    return {'status': 'ok'}" app.py

              nohup gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app:app &
              EOF
  )
  tags = { Name = "main-launch-template" }
}

resource "aws_autoscaling_group" "main" {
  name                = "playlist-bot-asg"
  vpc_zone_identifier = [aws_subnet.private_a.id, aws_subnet.private_c.id]
  launch_template {
    id      = aws_launch_template.main.id
    version = "$Latest"
  }
  min_size         = 2
  max_size         = 4
  desired_capacity = 2
  target_group_arns = [aws_lb_target_group.main.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 300
  tag {
    key                 = "Name"
    value               = "playlist-bot-ec2"
    propagate_at_launch = true
  }
}

# ------------------------------------------------------------------
# 6. S3 버킷 (프론트엔드 호스팅)
# ------------------------------------------------------------------
resource "aws_s3_bucket" "frontend_bucket" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_website_configuration" "frontend_website" {
  bucket = aws_s3_bucket.frontend_bucket.id
  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_policy" "allow_public_read" {
  bucket = aws_s3_bucket.frontend_bucket.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend_bucket.arn}/*"
    }]
  })
  depends_on = [aws_s3_bucket_public_access_block.frontend_bucket_access]
}

resource "aws_s3_bucket_public_access_block" "frontend_bucket_access" {
  bucket                  = aws_s3_bucket.frontend_bucket.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}