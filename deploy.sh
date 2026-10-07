#!/usr/bin/env bash
# ==============================================================================
# PulseGrid AI - Automated VM Deployment Script for Nebius AI Cloud
# ==============================================================================

set -e

echo "⚡ Starting PulseGrid AI Deployment on Nebius Cloud..."

# 1. Update system packages
sudo apt-get update -y
sudo apt-get install -y curl git ufw

# 2. Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# 3. Install Docker Compose plugin if not present
sudo apt-get install -y docker-compose-plugin docker-compose

# 4. Configure firewall for Streamlit (Port 8501)
echo "🛡️ Configuring Firewall for port 8501..."
sudo ufw allow 8501/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable || true

# 5. Build and launch container in background
echo "🚀 Building and starting PulseGrid AI container..."
docker compose down || true
docker compose up -d --build

# 6. Fetch Public IP
PUBLIC_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

echo "=================================================================="
echo "✅ PULSEGRID AI IS DEPLOYED AND RUNNING!"
echo "🌐 Access your application at:"
echo "   http://${PUBLIC_IP}:8501"
echo "=================================================================="
