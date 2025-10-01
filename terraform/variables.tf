variable "aws_region" {
  description = "배포할 AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

variable "vpc_cidr" {
  description = "VPC의 CIDR 블록"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_a_cidr" {
  description = "첫 번째 가용 영역(2a)의 Public Subnet CIDR"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_a_cidr" {
  description = "첫 번째 가용 영역(2a)의 Private Subnet CIDR"
  type        = string
  default     = "10.0.2.0/24"
}

variable "public_subnet_c_cidr" {
  description = "두 번째 가용 영역(2c)의 Public Subnet CIDR"
  type        = string
  default     = "10.0.3.0/24"
}

variable "private_subnet_c_cidr" {
  description = "두 번째 가용 영역(2c)의 Private Subnet CIDR"
  type        = string
  default     = "10.0.4.0/24"
}

variable "ec2_key_name" {
  description = "EC2 인스턴스에 연결할 키 페어의 이름"
  type        = string
}

variable "s3_bucket_name" {
  description = "프론트엔드 파일을 호스팅할 S3 버킷의 고유한 이름"
  type        = string
}

variable "instance_type" {
  description = "Auto Scaling Group에서 사용할 EC2 인스턴스 타입"
  type        = string
  default     = "t2.micro"
}