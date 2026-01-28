#!/bin/bash
# AWS Lightsail Deployment via AWS CLI
# Automates the entire deployment process from your local machine

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Stock Market AI Agent - AWS CLI Deployment${NC}"
echo "=================================================="
echo ""

# Configuration
INSTANCE_NAME="stock-market-ai-agent"
BUNDLE_ID="medium_2_0"  # $10/month: 2GB RAM, 1 vCPU, 60GB SSD
BLUEPRINT_ID="ubuntu_22_04"
AVAILABILITY_ZONE="us-east-1a"  # Change if needed
KEY_PAIR_NAME="stock-agent-key"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    echo ""
    echo "macOS: brew install awscli"
    echo "Linux: sudo apt-get install awscli"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured${NC}"
    echo "Run: aws configure"
    echo "You'll need:"
    echo "  - AWS Access Key ID"
    echo "  - AWS Secret Access Key"
    echo "  - Default region (e.g., us-east-1)"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI is configured${NC}"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account: $AWS_ACCOUNT"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Create .env file with your API keys first:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

echo -e "${GREEN}✅ .env file found${NC}"
echo ""

# Prompt for region
echo -e "${YELLOW}Select AWS Region:${NC}"
echo "1. us-east-1 (N. Virginia)"
echo "2. us-west-2 (Oregon)"
echo "3. eu-west-1 (Ireland)"
echo "4. ap-south-1 (Mumbai)"
echo "5. ap-southeast-1 (Singapore)"
read -p "Enter choice (1-5) [default: 1]: " region_choice

case $region_choice in
    2) REGION="us-west-2"; AVAILABILITY_ZONE="us-west-2a" ;;
    3) REGION="eu-west-1"; AVAILABILITY_ZONE="eu-west-1a" ;;
    4) REGION="ap-south-1"; AVAILABILITY_ZONE="ap-south-1a" ;;
    5) REGION="ap-southeast-1"; AVAILABILITY_ZONE="ap-southeast-1a" ;;
    *) REGION="us-east-1"; AVAILABILITY_ZONE="us-east-1a" ;;
esac

echo -e "${GREEN}Selected region: $REGION${NC}"
echo ""

# Check if instance already exists
echo -e "${BLUE}Checking for existing instance...${NC}"
EXISTING_INSTANCE=$(aws lightsail get-instances --region $REGION --query "instances[?name=='$INSTANCE_NAME'].name" --output text 2>/dev/null || echo "")

if [ ! -z "$EXISTING_INSTANCE" ]; then
    echo -e "${YELLOW}⚠️  Instance '$INSTANCE_NAME' already exists${NC}"
    read -p "Do you want to delete and recreate it? (y/n): " recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        echo "Deleting existing instance..."
        aws lightsail delete-instance --instance-name $INSTANCE_NAME --region $REGION
        echo "Waiting for deletion to complete (30 seconds)..."
        sleep 30
    else
        echo "Deployment cancelled"
        exit 0
    fi
fi

# Create SSH key pair if it doesn't exist
echo -e "${BLUE}Step 1: Creating SSH key pair...${NC}"
if ! aws lightsail get-key-pair --key-pair-name $KEY_PAIR_NAME --region $REGION &> /dev/null; then
    aws lightsail create-key-pair \
        --key-pair-name $KEY_PAIR_NAME \
        --region $REGION \
        --query 'privateKeyBase64' \
        --output text > ~/.ssh/${KEY_PAIR_NAME}.pem
    
    chmod 600 ~/.ssh/${KEY_PAIR_NAME}.pem
    echo -e "${GREEN}✅ SSH key created: ~/.ssh/${KEY_PAIR_NAME}.pem${NC}"
else
    echo -e "${GREEN}✅ SSH key already exists${NC}"
fi

# Create Lightsail instance
echo -e "${BLUE}Step 2: Creating Lightsail instance...${NC}"
aws lightsail create-instances \
    --instance-names $INSTANCE_NAME \
    --availability-zone $AVAILABILITY_ZONE \
    --blueprint-id $BLUEPRINT_ID \
    --bundle-id $BUNDLE_ID \
    --key-pair-name $KEY_PAIR_NAME \
    --region $REGION \
    --tags key=Project,value=StockMarketAI

echo -e "${GREEN}✅ Instance creation initiated${NC}"
echo "Waiting for instance to be ready (this takes 2-3 minutes)..."

# Wait for instance to be running
for i in {1..60}; do
    STATE=$(aws lightsail get-instance-state --instance-name $INSTANCE_NAME --region $REGION --query 'state.name' --output text 2>/dev/null || echo "pending")
    if [ "$STATE" == "running" ]; then
        echo -e "${GREEN}✅ Instance is running${NC}"
        break
    fi
    echo -n "."
    sleep 5
done
echo ""

# Get instance IP
INSTANCE_IP=$(aws lightsail get-instance --instance-name $INSTANCE_NAME --region $REGION --query 'instance.publicIpAddress' --output text)
echo -e "${GREEN}Instance IP: $INSTANCE_IP${NC}"

# Wait a bit more for SSH to be ready
echo "Waiting for SSH to be ready (30 seconds)..."
sleep 30

# Open firewall port 8501
echo -e "${BLUE}Step 3: Configuring firewall...${NC}"
aws lightsail put-instance-public-ports \
    --instance-name $INSTANCE_NAME \
    --port-infos fromPort=8501,toPort=8501,protocol=tcp \
    --region $REGION

echo -e "${GREEN}✅ Firewall configured (port 8501 open)${NC}"

# Create deployment package
echo -e "${BLUE}Step 4: Creating deployment package...${NC}"
TEMP_DIR=$(mktemp -d)
cp -r src requirements.txt Dockerfile docker-compose.yml .dockerignore run_web_ui.sh deploy.sh .env $TEMP_DIR/
cd $TEMP_DIR
tar -czf deployment.tar.gz *
cd - > /dev/null

echo -e "${GREEN}✅ Deployment package created${NC}"

# Upload files to instance
echo -e "${BLUE}Step 5: Uploading files to instance...${NC}"
SSH_KEY=~/.ssh/${KEY_PAIR_NAME}.pem

# Wait for SSH to be fully ready
echo "Testing SSH connection..."
for i in {1..12}; do
    if ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@$INSTANCE_IP "echo 'SSH ready'" &> /dev/null; then
        echo -e "${GREEN}✅ SSH connection established${NC}"
        break
    fi
    echo "Waiting for SSH... (attempt $i/12)"
    sleep 10
done

# Upload deployment package
scp -i $SSH_KEY -o StrictHostKeyChecking=no $TEMP_DIR/deployment.tar.gz ubuntu@$INSTANCE_IP:~/

# Clean up temp directory
rm -rf $TEMP_DIR

echo -e "${GREEN}✅ Files uploaded${NC}"

# Deploy on instance
echo -e "${BLUE}Step 6: Installing Docker and deploying application...${NC}"

ssh -i $SSH_KEY -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP << 'ENDSSH'
set -e

# Extract files
mkdir -p ~/stock-market-ai-agent
cd ~/stock-market-ai-agent
tar -xzf ~/deployment.tar.gz
rm ~/deployment.tar.gz

# Update system
echo "Updating system packages..."
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh > /dev/null 2>&1
rm get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Build and start application
echo "Building and starting application..."
sudo docker-compose up -d --build

echo "Deployment complete!"
ENDSSH

echo -e "${GREEN}✅ Application deployed${NC}"

# Wait for application to start
echo "Waiting for application to start (30 seconds)..."
sleep 30

# Test application
echo -e "${BLUE}Step 7: Testing application...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://$INSTANCE_IP:8501/_stcore/health | grep -q "200"; then
    echo -e "${GREEN}✅ Application is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Application may still be starting...${NC}"
fi

# Display summary
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo "Instance Details:"
echo "  Name:       $INSTANCE_NAME"
echo "  Region:     $REGION"
echo "  IP Address: $INSTANCE_IP"
echo "  SSH Key:    ~/.ssh/${KEY_PAIR_NAME}.pem"
echo ""
echo "Access your application at:"
echo -e "  ${BLUE}http://$INSTANCE_IP:8501${NC}"
echo ""
echo "SSH into your instance:"
echo "  ssh -i ~/.ssh/${KEY_PAIR_NAME}.pem ubuntu@$INSTANCE_IP"
echo ""
echo "Useful commands on the instance:"
echo "  cd ~/stock-market-ai-agent"
echo "  sudo docker-compose logs -f        # View logs"
echo "  sudo docker-compose restart        # Restart app"
echo "  sudo docker ps                     # Check status"
echo ""
echo "To delete the instance:"
echo "  aws lightsail delete-instance --instance-name $INSTANCE_NAME --region $REGION"
echo ""
