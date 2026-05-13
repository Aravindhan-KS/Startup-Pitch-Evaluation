#!/bin/bash
# EC2 user data — runs once at first boot as root
# Installs Docker + Compose plugin so deploy.sh can SSH in and docker compose up
set -euo pipefail

# ── System update & Docker install ──────────────────────────────────────────────
dnf update -y
dnf install -y docker amazon-ecr-credential-helper

systemctl enable --now docker
usermod -aG docker ec2-user

# ── Docker Compose v2 plugin ─────────────────────────────────────────────────────
mkdir -p /usr/local/lib/docker/cli-plugins
curl -fsSL \
  "https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# ── ECR credential helper for ec2-user ──────────────────────────────────────────
# Lets 'docker pull' authenticate automatically via the instance IAM role.
# Terraform templatefile substitutes ${aws_region} before this script runs.
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
mkdir -p /home/ec2-user/.docker

if [ -n "$ACCOUNT_ID" ]; then
  printf '{"credHelpers":{"%s.dkr.ecr.${aws_region}.amazonaws.com":"ecr-login"}}\n' \
    "$ACCOUNT_ID" > /home/ec2-user/.docker/config.json
else
  printf '{"credHelpers":{"public.ecr.aws":"ecr-login"}}\n' \
    > /home/ec2-user/.docker/config.json
fi

chown -R ec2-user:ec2-user /home/ec2-user/.docker

# ── App directory ────────────────────────────────────────────────────────────────
mkdir -p /opt/pitch-eval
chown ec2-user:ec2-user /opt/pitch-eval

echo "User data bootstrap complete"
