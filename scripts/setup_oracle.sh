#!/bin/bash

# Project Acheron - Oracle Cloud VPS Setup Script
# Automates the initial setup of Oracle Cloud Free Tier VPS

set -e

echo "============================================"
echo "  ORACLE CLOUD VPS SETUP FOR ACHERON"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running on Oracle Cloud (Ubuntu/Debian)
if [ ! -f /etc/os-release ]; then
    echo -e "${RED}❌ Cannot detect OS${NC}"
    exit 1
fi

. /etc/os-release

echo "Detected OS: $NAME $VERSION"
echo ""

# Update system
echo "Step 1/8: Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y
echo -e "${GREEN}✅ System updated${NC}"
echo ""

# Install essential tools
echo "Step 2/8: Installing essential tools..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    htop \
    vim
echo -e "${GREEN}✅ Essential tools installed${NC}"
echo ""

# Install Docker
echo "Step 3/8: Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi
echo ""

# Install Docker Compose
echo "Step 4/8: Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
else
    echo -e "${GREEN}✅ Docker Compose already installed${NC}"
fi
echo ""

# Configure firewall (UFW)
echo "Step 5/8: Configuring firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 22/tcp
echo -e "${GREEN}✅ Firewall configured${NC}"
echo ""

# Optimize for Oracle Cloud ARM (if ARM architecture)
echo "Step 6/8: Optimizing system settings..."

# Increase file descriptors limit
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize TCP settings for WebSocket connections
sudo tee -a /etc/sysctl.conf > /dev/null <<EOF

# Acheron optimizations
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
EOF

sudo sysctl -p

echo -e "${GREEN}✅ System optimized${NC}"
echo ""

# Set up automatic updates (Oracle Cloud specific)
echo "Step 7/8: Configuring automatic security updates..."
sudo apt-get install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
echo -e "${GREEN}✅ Automatic updates configured${NC}"
echo ""

# Clone or setup project directory
echo "Step 8/8: Setting up project directory..."

if [ ! -d "$HOME/pinnacle-scraper" ]; then
    mkdir -p $HOME/pinnacle-scraper
    echo "Created project directory: $HOME/pinnacle-scraper"
fi

cd $HOME/pinnacle-scraper

echo -e "${GREEN}✅ Project directory ready${NC}"
echo ""

# Print next steps
echo "============================================"
echo -e "${GREEN}✅ ORACLE CLOUD VPS SETUP COMPLETE${NC}"
echo "============================================"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Log out and log back in for Docker permissions:"
echo "   exit"
echo "   ssh [your-server]"
echo ""
echo "2. Upload Project Acheron files:"
echo "   scp -r /path/to/pinnacle-scraper/* [your-server]:~/pinnacle-scraper/"
echo ""
echo "3. Edit configuration:"
echo "   cd ~/pinnacle-scraper"
echo "   nano config.yaml"
echo ""
echo "4. Run deployment:"
echo "   ./scripts/deploy.sh"
echo ""
echo "============================================"
echo ""
echo "📊 System Information:"
echo "  CPU: $(nproc) cores"
echo "  RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  Disk: $(df -h / | awk 'NR==2 {print $2}')"
echo "  IP: $(hostname -I | awk '{print $1}')"
echo ""
echo "============================================"
