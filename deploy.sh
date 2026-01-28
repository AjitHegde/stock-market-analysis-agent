#!/bin/bash
# AWS Lightsail Deployment Script for Stock Market AI Agent

set -e  # Exit on error

echo "🚀 Stock Market AI Agent - AWS Lightsail Deployment"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Lightsail instance
if [ ! -f /etc/lightsail-release ] && [ ! -f /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json ]; then
    echo -e "${YELLOW}⚠️  Warning: This script is designed for AWS Lightsail instances${NC}"
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Update system packages
echo -e "${GREEN}Step 1: Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}Step 2: Installing Docker...${NC}"
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    # Start Docker service
    sudo systemctl start docker
    sudo systemctl enable docker
    
    echo -e "${GREEN}✅ Docker installed successfully${NC}"
    echo -e "${YELLOW}⚠️  You may need to log out and back in for docker group changes to take effect${NC}"
else
    echo -e "${GREEN}✅ Docker is already installed${NC}"
fi

# Step 3: Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}Step 3: Installing Docker Compose...${NC}"
    
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo -e "${GREEN}✅ Docker Compose installed successfully${NC}"
else
    echo -e "${GREEN}✅ Docker Compose is already installed${NC}"
fi

# Step 4: Check for .env file
echo -e "${GREEN}Step 4: Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create a .env file with your API keys."
    echo "You can copy .env.example and fill in your keys:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
else
    echo -e "${GREEN}✅ .env file found${NC}"
fi

# Step 5: Create data directory
echo -e "${GREEN}Step 5: Creating data directory...${NC}"
mkdir -p data
echo -e "${GREEN}✅ Data directory created${NC}"

# Step 6: Build Docker image
echo -e "${GREEN}Step 6: Building Docker image...${NC}"
docker-compose build

# Step 7: Stop existing container if running
echo -e "${GREEN}Step 7: Stopping existing container (if any)...${NC}"
docker-compose down || true

# Step 8: Start the application
echo -e "${GREEN}Step 8: Starting the application...${NC}"
docker-compose up -d

# Step 9: Wait for application to be ready
echo -e "${GREEN}Step 9: Waiting for application to start...${NC}"
sleep 10

# Check if container is running
if docker ps | grep -q stock-market-ai-agent; then
    echo -e "${GREEN}✅ Container is running${NC}"
else
    echo -e "${RED}❌ Container failed to start${NC}"
    echo "Check logs with: docker-compose logs"
    exit 1
fi

# Step 10: Display access information
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo "Your Stock Market AI Agent is now running!"
echo ""
echo "Access the application at:"
echo "  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop application: docker-compose down"
echo "  Restart:          docker-compose restart"
echo "  Update code:      git pull && docker-compose up -d --build"
echo ""
echo -e "${YELLOW}⚠️  Remember to configure your Lightsail firewall to allow port 8501${NC}"
echo ""
