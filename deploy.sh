#!/usr/bin/env bash
# deploy.sh — build images, push to ECR, and run containers on EC2 via Terraform
# Usage: ./deploy.sh [--destroy]
#
# Prerequisites:
#   - aws cli v2 configured (aws configure or env vars)
#   - terraform >= 1.6
#   - docker (with buildx)
#   - SSH key pair at ~/.ssh/id_rsa (or set SSH_KEY env var)
#   - firebase_key.json in project root
#   - secrets.toml  in project root (Streamlit Firebase secrets)
#
# secrets.toml format:
#   [firebase]
#   type = "service_account"
#   project_id = "..."
#   private_key_id = "..."
#   private_key = "<your-private-key-contents>"
#   client_email = "..."
#   client_id = "..."
#   auth_uri = "https://accounts.google.com/o/oauth2/auth"
#   token_uri = "https://oauth2.googleapis.com/token"
#   auth_provider_x509_cert_url = "..."
#   client_x509_cert_url = "..."

set -euo pipefail

# ── Config ───────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"
INFRA_DIR="$SCRIPT_DIR/infra"
FIREBASE_KEY="${FIREBASE_KEY:-$HOME/code/hostel/firebase_key.json}"

# ── Helpers ──────────────────────────────────────────────────────────────────────
info() { echo "  [deploy] $*"; }
error() {
	echo "  [deploy] ERROR: $*" >&2
	exit 1
}

# ── Destroy mode ─────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--destroy" ]]; then
	info "Running terraform destroy..."
	terraform -chdir="$INFRA_DIR" destroy -auto-approve
	info "All resources removed."
	exit 0
fi

# ── Preflight checks ──────────────────────────────────────────────────────────────
command -v aws >/dev/null 2>&1 || error "aws cli not found. Install from https://aws.amazon.com/cli/"
command -v terraform >/dev/null 2>&1 || error "terraform not found. Install from https://developer.hashicorp.com/terraform/downloads"
command -v docker >/dev/null 2>&1 || error "docker not found."

[[ -f "$SSH_KEY" ]] || error "SSH private key not found at $SSH_KEY. Set SSH_KEY env var or generate one."
[[ -f "$FIREBASE_KEY" ]] || error "firebase_key.json not found at $FIREBASE_KEY. Set FIREBASE_KEY env var to override."
[[ -f "$SCRIPT_DIR/secrets.toml" ]] || error "secrets.toml not found in project root. See header comment for format."

# ── Terraform: provision infrastructure ──────────────────────────────────────────
info "Initialising Terraform..."
terraform -chdir="$INFRA_DIR" init -upgrade -input=false

info "Applying Terraform (this creates ECR + EC2 on first run, ~2 min)..."
terraform -chdir="$INFRA_DIR" apply -auto-approve -input=false

# ── Grab outputs ─────────────────────────────────────────────────────────────────
ECR_REGISTRY=$(terraform -chdir="$INFRA_DIR" output -raw ecr_registry)
ECR_BACKEND=$(terraform -chdir="$INFRA_DIR" output -raw ecr_backend_url)
ECR_STREAMLIT=$(terraform -chdir="$INFRA_DIR" output -raw ecr_streamlit_url)
ECR_NGINX=$(terraform -chdir="$INFRA_DIR" output -raw ecr_nginx_url)
INSTANCE_IP=$(terraform -chdir="$INFRA_DIR" output -raw instance_public_ip)
AWS_REGION=$(terraform -chdir="$INFRA_DIR" output -raw aws_region)

info "ECR registry : $ECR_REGISTRY"
info "Instance IP  : $INSTANCE_IP"

# ── Docker login to ECR ──────────────────────────────────────────────────────────
info "Authenticating Docker with ECR..."
aws ecr get-login-password --region "$AWS_REGION" |
	docker login --username AWS --password-stdin "$ECR_REGISTRY"

# ── Build & push images ──────────────────────────────────────────────────────────
info "Building backend image (this is slow once due to PyTorch CPU wheel)..."
docker build \
	--platform linux/amd64 \
	-t "$ECR_BACKEND:latest" \
	-f "$SCRIPT_DIR/Dockerfile.backend" \
	"$SCRIPT_DIR"

info "Building streamlit image..."
docker build \
	--platform linux/amd64 \
	-t "$ECR_STREAMLIT:latest" \
	-f "$SCRIPT_DIR/Dockerfile.streamlit" \
	"$SCRIPT_DIR"

info "Building nginx image..."
docker build \
	--platform linux/amd64 \
	-t "$ECR_NGINX:latest" \
	-f "$SCRIPT_DIR/Dockerfile.nginx" \
	"$SCRIPT_DIR"

info "Pushing images to ECR..."
docker push "$ECR_BACKEND:latest"
docker push "$ECR_STREAMLIT:latest"
docker push "$ECR_NGINX:latest"

# ── Generate compose .env for EC2 ────────────────────────────────────────────────
info "Generating deploy env file..."
cat >/tmp/pitch-eval.env <<ENV
ECR_REGISTRY=${ECR_REGISTRY}
SPE_USE_HEURISTIC_PIPELINE=true
SPE_USE_LOCAL_TRANSCRIBER=true
SPE_ENABLE_VISUAL_EXTRACTION=true
SPE_ENABLE_AUDIO_EXTRACTION=true
ENV

# ── Wait for EC2 SSH to be ready ─────────────────────────────────────────────────
info "Waiting for EC2 SSH to become available..."
for i in $(seq 1 30); do
	if ssh -i "$SSH_KEY" \
		-o StrictHostKeyChecking=no \
		-o ConnectTimeout=5 \
		-o BatchMode=yes \
		ec2-user@"$INSTANCE_IP" "exit 0" 2>/dev/null; then
		break
	fi
	echo "  [deploy] Attempt $i/30 — retrying in 10s..."
	sleep 10
done

SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no"

# ── Copy deployment files to EC2 ─────────────────────────────────────────────────
info "Copying files to EC2..."
scp $SSH_OPTS \
	"$SCRIPT_DIR/docker-compose.yml" \
	"$FIREBASE_KEY" \
	"$SCRIPT_DIR/secrets.toml" \
	/tmp/pitch-eval.env \
	ec2-user@"$INSTANCE_IP":/opt/pitch-eval/

# Rename the env file to .env (docker-compose picks it up automatically)
ssh $SSH_OPTS ec2-user@"$INSTANCE_IP" \
	"mv /opt/pitch-eval/pitch-eval.env /opt/pitch-eval/.env"

# ── Pull images on EC2 & start containers ────────────────────────────────────────
info "Starting containers on EC2..."
ssh $SSH_OPTS ec2-user@"$INSTANCE_IP" <<REMOTE
  set -e
  cd /opt/pitch-eval

  # Authenticate with ECR using the instance IAM role
  aws ecr get-login-password --region ${AWS_REGION} \
    | docker login --username AWS --password-stdin ${ECR_REGISTRY}

  # Pull latest images
  docker compose pull

  # Restart stack (graceful: stops old, starts new)
  docker compose up -d --remove-orphans

  echo "Containers running:"
  docker compose ps
REMOTE

# ── Done ─────────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Deployment complete"
echo ""
echo "  App         → http://${INSTANCE_IP}"
echo "  Dashboard   → http://${INSTANCE_IP}:8501"
echo "  SSH         → ssh -i ${SSH_KEY} ec2-user@${INSTANCE_IP}"
echo ""
echo "  To tear down: ./deploy.sh --destroy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
