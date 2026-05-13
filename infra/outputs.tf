output "instance_public_ip" {
  description = "Public IP of the EC2 instance (stable Elastic IP)"
  value       = aws_eip.app.public_ip
}

output "app_url" {
  description = "Main application URL (FastAPI + frontend)"
  value       = "http://${aws_eip.app.public_ip}"
}

output "dashboard_url" {
  description = "Streamlit dashboard URL"
  value       = "http://${aws_eip.app.public_ip}:8501"
}

output "ecr_backend_url" {
  description = "Full ECR URI for the backend image"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_streamlit_url" {
  description = "Full ECR URI for the streamlit image"
  value       = aws_ecr_repository.streamlit.repository_url
}

output "ecr_nginx_url" {
  description = "Full ECR URI for the nginx image"
  value       = aws_ecr_repository.nginx.repository_url
}

output "ecr_registry" {
  description = "ECR registry hostname (account.dkr.ecr.region.amazonaws.com)"
  value       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com"
}

output "aws_region" {
  description = "Deployed region"
  value       = var.aws_region
}

output "instance_id" {
  description = "EC2 instance ID (for aws CLI operations)"
  value       = aws_instance.app.id
}
