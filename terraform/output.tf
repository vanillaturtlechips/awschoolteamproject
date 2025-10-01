output "frontend_url" {
  description = "프론트엔드 접속 주소 (이 주소로 접속하세요!)"
  value       = "http://${aws_s3_bucket_website_configuration.frontend_website.website_endpoint}"
}

output "backend_url" {
  description = "백엔드 로드 밸런서 주소 (API 요청에 사용)"
  value       = "http://${aws_lb.main.dns_name}"
}