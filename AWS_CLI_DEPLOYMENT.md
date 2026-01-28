# AWS CLI Deployment Guide

Automated deployment to AWS Lightsail using AWS CLI from your local machine.

## Prerequisites

### 1. Install AWS CLI

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
sudo apt-get install awscli
```

**Windows:**
Download from: https://aws.amazon.com/cli/

**Verify installation:**
```bash
aws --version
```

### 2. Configure AWS CLI

You need AWS credentials (Access Key ID and Secret Access Key).

**Get credentials:**
1. Log into AWS Console
2. Go to IAM → Users → Your User → Security Credentials
3. Create Access Key → CLI
4. Save the Access Key ID and Secret Access Key

**Configure AWS CLI:**
```bash
aws configure
```

Enter:
- AWS Access Key ID: `YOUR_ACCESS_KEY`
- AWS Secret Access Key: `YOUR_SECRET_KEY`
- Default region: `us-east-1` (or your preferred region)
- Default output format: `json`

**Verify configuration:**
```bash
aws sts get-caller-identity
```

### 3. Prepare Environment File

```bash
# Create .env file with your API keys
cp .env.example .env
nano .env  # Add your API keys
```

## Automated Deployment

### One-Command Deployment

```bash
./deploy-aws-cli.sh
```

This script will:
1. ✅ Check AWS CLI configuration
2. ✅ Create SSH key pair
3. ✅ Create Lightsail instance ($10/month)
4. ✅ Configure firewall (port 8501)
5. ✅ Upload application files
6. ✅ Install Docker on instance
7. ✅ Build and start application
8. ✅ Test application health

**Total time:** 5-7 minutes

### What the Script Does

```
┌─────────────────────────────────────────┐
│     Your Local Machine                  │
│                                         │
│  1. Validates AWS CLI setup             │
│  2. Creates deployment package          │
│  3. Creates Lightsail instance          │
│  4. Uploads files via SCP               │
│  5. Runs deployment via SSH             │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│     AWS Lightsail Instance              │
│                                         │
│  1. Receives deployment package         │
│  2. Installs Docker                     │
│  3. Builds container                    │
│  4. Starts application                  │
└─────────────────────────────────────────┘
```

## Region Selection

During deployment, you'll be prompted to select a region:

```
1. us-east-1 (N. Virginia) - Default
2. us-west-2 (Oregon)
3. eu-west-1 (Ireland)
4. ap-south-1 (Mumbai)
5. ap-southeast-1 (Singapore)
```

Choose the region closest to you for best performance.

## After Deployment

### Access Your Application

The script will display:
```
Access your application at:
  http://YOUR_IP:8501
```

Open this URL in your browser.

### SSH into Instance

```bash
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP
```

### View Logs

```bash
# SSH into instance first
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP

# Then view logs
cd ~/stock-market-ai-agent
sudo docker-compose logs -f
```

### Manage Application

```bash
# Restart
sudo docker-compose restart

# Stop
sudo docker-compose down

# Start
sudo docker-compose up -d

# Rebuild
sudo docker-compose up -d --build
```

## Manual AWS CLI Commands

If you prefer manual control:

### Create Instance

```bash
aws lightsail create-instances \
  --instance-names stock-market-ai-agent \
  --availability-zone us-east-1a \
  --blueprint-id ubuntu_22_04 \
  --bundle-id medium_2_0 \
  --region us-east-1
```

### Get Instance IP

```bash
aws lightsail get-instance \
  --instance-name stock-market-ai-agent \
  --region us-east-1 \
  --query 'instance.publicIpAddress' \
  --output text
```

### Open Firewall Port

```bash
aws lightsail put-instance-public-ports \
  --instance-name stock-market-ai-agent \
  --port-infos fromPort=8501,toPort=8501,protocol=tcp \
  --region us-east-1
```

### Create Snapshot

```bash
aws lightsail create-instance-snapshot \
  --instance-name stock-market-ai-agent \
  --instance-snapshot-name stock-agent-$(date +%Y%m%d) \
  --region us-east-1
```

### Delete Instance

```bash
aws lightsail delete-instance \
  --instance-name stock-market-ai-agent \
  --region us-east-1
```

### List Instances

```bash
aws lightsail get-instances --region us-east-1
```

## Troubleshooting

### AWS CLI Not Configured

```bash
aws configure
# Enter your credentials
```

### Permission Denied

Make sure your AWS user has Lightsail permissions:
- AmazonLightsailFullAccess (or custom policy)

### SSH Connection Failed

```bash
# Wait longer for instance to be ready
sleep 60

# Try SSH again
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP
```

### Instance Already Exists

The script will prompt you to delete and recreate, or you can manually delete:

```bash
aws lightsail delete-instance \
  --instance-name stock-market-ai-agent \
  --region us-east-1
```

### Application Not Starting

SSH into instance and check logs:

```bash
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP
cd ~/stock-market-ai-agent
sudo docker-compose logs
```

## Cost Management

### Check Current Costs

```bash
# List all instances
aws lightsail get-instances --region us-east-1

# Get instance details
aws lightsail get-instance \
  --instance-name stock-market-ai-agent \
  --region us-east-1
```

### Stop Instance (Still Charged)

Lightsail charges even when stopped. To save costs, delete the instance:

```bash
# Create snapshot first
aws lightsail create-instance-snapshot \
  --instance-name stock-market-ai-agent \
  --instance-snapshot-name stock-agent-backup \
  --region us-east-1

# Delete instance
aws lightsail delete-instance \
  --instance-name stock-market-ai-agent \
  --region us-east-1
```

### Restore from Snapshot

```bash
aws lightsail create-instances-from-snapshot \
  --instance-names stock-market-ai-agent \
  --instance-snapshot-name stock-agent-backup \
  --availability-zone us-east-1a \
  --bundle-id medium_2_0 \
  --region us-east-1
```

## Advanced Usage

### Deploy to Multiple Regions

```bash
# Deploy to us-east-1
./deploy-aws-cli.sh
# Select region 1

# Deploy to eu-west-1
./deploy-aws-cli.sh
# Select region 3
```

### Custom Instance Name

Edit `deploy-aws-cli.sh`:
```bash
INSTANCE_NAME="my-custom-name"
```

### Different Instance Size

Edit `deploy-aws-cli.sh`:
```bash
# $5/month: 512MB RAM
BUNDLE_ID="nano_2_0"

# $10/month: 2GB RAM (default)
BUNDLE_ID="medium_2_0"

# $20/month: 4GB RAM
BUNDLE_ID="large_2_0"
```

## Comparison: AWS CLI vs Manual

| Method | Time | Complexity | Automation |
|--------|------|------------|------------|
| **AWS CLI Script** | 5-7 min | Low | Full |
| **Manual Console** | 15-20 min | Medium | Partial |
| **Manual SSH** | 20-30 min | High | None |

**Recommendation:** Use AWS CLI script for fastest, most reliable deployment.

## Security Best Practices

### 1. Secure SSH Key

```bash
# Key is automatically created at:
~/.ssh/stock-agent-key.pem

# Verify permissions
ls -l ~/.ssh/stock-agent-key.pem
# Should show: -rw------- (600)
```

### 2. Rotate Access Keys

Rotate your AWS access keys every 90 days:
1. Create new access key in IAM
2. Update with `aws configure`
3. Delete old access key

### 3. Use IAM Roles (Advanced)

Instead of access keys, use IAM roles with temporary credentials.

## Monitoring

### CloudWatch Metrics

Enable CloudWatch metrics in Lightsail console for:
- CPU utilization
- Network traffic
- Disk I/O

### Set Up Alarms

```bash
# Create alarm for high CPU
aws lightsail put-alarm \
  --alarm-name high-cpu \
  --monitored-resource-name stock-market-ai-agent \
  --metric-name CPUUtilization \
  --comparison-operator GreaterThanThreshold \
  --threshold 80 \
  --evaluation-periods 2
```

## Backup Strategy

### Automated Snapshots

```bash
# Enable automatic snapshots (via console)
# Or create manual snapshots regularly

# Create snapshot
aws lightsail create-instance-snapshot \
  --instance-name stock-market-ai-agent \
  --instance-snapshot-name stock-agent-$(date +%Y%m%d-%H%M) \
  --region us-east-1

# List snapshots
aws lightsail get-instance-snapshots --region us-east-1

# Delete old snapshots
aws lightsail delete-instance-snapshot \
  --instance-snapshot-name stock-agent-20250101 \
  --region us-east-1
```

## Summary

### Advantages of AWS CLI Deployment

- ✅ **Fast**: 5-7 minutes total
- ✅ **Automated**: One command deployment
- ✅ **Repeatable**: Same process every time
- ✅ **Scriptable**: Can integrate into CI/CD
- ✅ **Version Controlled**: Script in git

### Quick Commands Reference

```bash
# Deploy
./deploy-aws-cli.sh

# SSH
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP

# Delete
aws lightsail delete-instance --instance-name stock-market-ai-agent --region us-east-1

# Snapshot
aws lightsail create-instance-snapshot --instance-name stock-market-ai-agent --instance-snapshot-name backup-$(date +%Y%m%d) --region us-east-1
```

---

**Ready to deploy?** Run `./deploy-aws-cli.sh` and follow the prompts! 🚀
