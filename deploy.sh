#!/bin/bash
# One-time (or repeatable) deploy bootstrap for a fresh EC2 instance.
#
# Usage:
#   ./deploy.sh [s3-bucket-name]
#
# The bucket name is auto-detected from ~/.bookshop-bucket-name (written by
# terraform's user_data on instance creation). Pass it explicitly only if
# that file is missing (e.g. an older instance) or you want to override it.
set -euo pipefail

BUCKET_NAME="${1:-}"

if [ -z "$BUCKET_NAME" ] && [ -f "$HOME/.bookshop-bucket-name" ]; then
  BUCKET_NAME=$(cat "$HOME/.bookshop-bucket-name")
fi

if [ -z "$BUCKET_NAME" ]; then
  echo "Usage: ./deploy.sh [s3-bucket-name]"
  echo "  Could not auto-detect it from ~/.bookshop-bucket-name."
  echo "  Get it with: terraform output s3_bucket_name"
  exit 1
fi

if [ ! -f .env ]; then
  cp env-sample .env
  echo ".env created from env-sample."
  echo "Fill in SECRET_KEY, Stripe keys and (optionally) email settings, then re-run this script."
  exit 1
fi

# Required values that can't be auto-generated — must already be filled in .env.
REQUIRED_VARS=(SECRET_KEY STRIPE_PUBLIC_KEY STRIPE_SECRET_KEY STRIPE_WEBHOOK_SECRET)
PLACEHOLDERS=(django-insecure-change-me-in-production pk_test_... sk_test_... whsec_...)

missing=()
for key in "${REQUIRED_VARS[@]}"; do
  value=$(grep "^${key}=" .env | cut -d '=' -f2- || true)
  is_placeholder=false
  for placeholder in "${PLACEHOLDERS[@]}"; do
    if [ "$value" = "$placeholder" ]; then
      is_placeholder=true
    fi
  done
  if [ -z "$value" ] || [ "$is_placeholder" = true ]; then
    missing+=("$key")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Missing or unfilled in .env: ${missing[*]}"
  echo "Fill these in .env before deploying."
  exit 1
fi

TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)

set_env() {
  local key="$1" value="$2"
  if grep -q "^${key}=" .env; then
    sed -i "s|^${key}=.*|${key}=${value}|" .env
  else
    echo "${key}=${value}" >>.env
  fi
}

echo "Public IP: $PUBLIC_IP"
echo "S3 bucket: $BUCKET_NAME"

set_env "DEBUG" "false"
set_env "AWS_STORAGE_BUCKET_NAME" "$BUCKET_NAME"
set_env "AWS_S3_REGION_NAME" "us-east-1"
set_env "ALLOWED_HOSTS" "${PUBLIC_IP},localhost,127.0.0.1,0.0.0.0,web"

docker compose up --build -d

# staticfiles/ is bind-mounted from the host, which shadows whatever collectstatic
# produced inside the image at build time — must re-run it once the volume is live.
docker compose exec -T web python manage.py collectstatic --noinput

if ! command -v nginx &>/dev/null; then
  sudo apt-get update
  sudo apt-get install -y nginx
fi

sudo cp nginx.conf /etc/nginx/sites-available/bookshop
sudo ln -sf /etc/nginx/sites-available/bookshop /etc/nginx/sites-enabled/bookshop
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

echo "Done. App should be live at http://${PUBLIC_IP}/"
