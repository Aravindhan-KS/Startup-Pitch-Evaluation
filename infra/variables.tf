variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix applied to every resource name"
  type        = string
  default     = "pitch-eval"
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key uploaded to EC2 as the deploy key pair"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}
