#!/bin/bash

# Project Acheron - One-Click Deployment Script
# This script automates the deployment process on Oracle Cloud or any VPS

set -e  # Exit on error

echo "============================================"
echo "  PROJECT ACHERON - DEPLOYMENT SCRIPT"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}⚠️  Please do not run this script as root${NC}"
    exit 1
fi

# Step 1: Check prerequisites
echo "Step 1/6: Checking prerequisites..."

command -v docker >/dev/null 2>&1 || {
    echo -e "${YELLOW}Docker not found. Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker installed${NC}"
    echo -e "${YELLOW}⚠️  Please log out and log back in for Docker permissions to take effect${NC}"
    echo -e "${YELLOW}Then run this script again.${NC}"
    exit 0
}

command -v docker-compose >/dev/null 2>&1 || {
    echo -e "${YELLOW}Docker Compose not found. Installing...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
}

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Step 2: Check configuration
echo "Step 2/6: Checking configuration..."

if [ ! -f "config.yaml" ]; then
    echo -e "${RED}❌ config.yaml not found!${NC}"
    echo "Please create config.yaml from the template and fill in your credentials."
    exit 1
fi

# Check if config has been edited (contains YOUR_)
if grep -q "YOUR_PINNACLE_USERNAME" config.yaml; then
    echo -e "${RED}❌ config.yaml not configured!${NC}"
    echo "Please edit config.yaml and fill in your Pinnacle credentials and API keys."
    exit 1
fi

echo -e "${GREEN}✅ Configuration file found${NC}"
echo ""

# Step 3: Create necessary directories
echo "Step 3/6: Creating directories..."

mkdir -p logs
chmod 755 logs

echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Step 4: Pull/Build Docker images
echo "Step 4/6: Building Docker images (this may take a few minutes)..."

docker-compose build

echo -e "${GREEN}✅ Docker images built${NC}"
echo ""

# Step 5: Start services
echo "Step 5/6: Starting services..."

docker-compose up -d

echo -e "${GREEN}✅ Services started${NC}"
echo ""

# Step 6: Wait for services to be healthy
echo "Step 6/6: Waiting for services to be ready..."

echo "Waiting for Redis..."
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis is ready${NC}"
        break
    fi
    sleep 1
done

echo ""
echo "============================================"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo "============================================"
echo ""
echo "Project Acheron is now running!"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f acheron"
echo ""
echo "🔍 Check status:"
echo "   docker-compose ps"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "📱 Notifications will be sent to:"
echo "   https://ntfy.sh/$(grep 'topic:' config.yaml | awk '{print $2}' | tr -d '"')"
echo ""
echo "============================================"
echo ""

# Show initial logs
echo "📋 Last 50 log lines:"
echo ""
docker-compose logs --tail=50 acheron

echo ""
echo -e "${GREEN}Press Ctrl+C to stop viewing logs (services will continue running)${NC}"
echo ""

# Follow logs
docker-compose logs -f acheron
