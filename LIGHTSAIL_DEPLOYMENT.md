# AWS Lightsail Deployment Guide

Complete guide for deploying the Stock Market AI Agent to AWS Lightsail for fast, consistent performance.

## Why Lightsail?

- **Fast Response**: 25-30 second analysis time with no cold starts
- **Consistent Performance**: Always-on server, no initialization delays
- **Cost-Effective**: $10/month for 2GB RAM, 1 vCPU, 60GB SSD
- **Simple Setup**: Easier than EC2, includes static IP and firewall management
- **Scalable**: Can upgrade to larger instances as needed

---

## Prerequisites

Before you begin, ensure you have:

1. **AWS Account** - Sign up at https://aws.amazon.com/
2. **API Keys** - Obtain keys from:
   - News API: https://newsapi.org/
   - Finnhub: https://finnhub.io/
   - Alpha Vantage: https://www.alphavantage.co/
   - (Optional) Twitter API, Reddit API
3. **SSH Client** - Terminal (Mac/Linux) or PuTTY (Windows)
4. **Git** (optional) - For cloning the repository

---

## Deployment Steps

### Step 1: Create Lightsail Instance

1. **Log in to AWS Console**
   - Go to https://lightsail.aws.amazon.com/

2. **Create Instance**
   - Click "Create instance"
   - Select **Instance location**: Choose region closest to you
   - Select **Platform**: Linux/Unix
   - Select **Blueprint**: OS Only → Ubuntu 22.04 LTS

3. **Choose Instance Plan**
   - Select **$10/month plan**:
     - 2 GB RAM
     - 1 vCPU
     - 60 GB SSD
     - 3 TB transfer

4. **Configure Instance**
   - **Instance name**: `stock-market-ai-agent`
   - Click "Create instance"

5. **Wait for Instance to Start**
   - Status will change from "Pending" to "Running" (1-2 minutes)

### Step 2: Configure Firewall

1. **Open Networking Tab**
   - Click on your instance
   - Go to "Networking" tab

2. **Add Firewall Rule**
   - Click "Add rule"
   - **Application**: Custom
   - **Protocol**: TCP
   - **Port**: 8501
   - **Source**: Anywhere (0.0.0.0/0)
   - Click "Create"

3. **Note Your Static IP**
   - Your instance has a static IP by default
   - Note this IP address (e.g., 54.123.45.67)

### Step 3: Connect to Instance

1. **SSH into Instance**
   
   **Option A: Browser-based SSH (Easiest)**
   - Click "Connect using SSH" button in Lightsail console
   
   **Option B: SSH from Terminal**
   ```bash
   # Download SSH key from Lightsail console first
   ssh -i /path/to/LightsailDefaultKey.pem ubuntu@YOUR_INSTANCE_IP
   ```

2. **Update System**
   ```bash
   sudo apt-get update
   sudo apt-get upgrade -y
   ```

### Step 4: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

**Important**: Log out and back in for docker group changes to take effect:
```bash
exit
# Then SSH back in
```

### Step 5: Deploy Application

1. **Clone Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/stock-market-ai-agent.git
   cd stock-market-ai-agent
   ```
   
   **OR Upload Files Manually**
   ```bash
   # Create directory
   mkdir -p ~/stock-market-ai-agent
   cd ~/stock-market-ai-agent
   
   # Upload files using SCP or SFTP
   # From your local machine:
   scp -i /path/to/LightsailDefaultKey.pem -r ./* ubuntu@YOUR_INSTANCE_IP:~/stock-market-ai-agent/
   ```

2. **Configure Environment Variables**
   ```bash
   # Copy example file
   cp .env.example .env
   
   # Edit with your API keys
   nano .env
   ```
   
   Add your API keys:
   ```
   NEWS_API_KEY=your_actual_key_here
   FINNHUB_API_KEY=your_actual_key_here
   ALPHA_VANTAGE_API_KEY=your_actual_key_here
   TWITTER_API_KEY=your_actual_key_here
   REDDIT_API_KEY=your_actual_key_here
   ```
   
   Save and exit (Ctrl+X, then Y, then Enter)

3. **Run Deployment Script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
   
   **OR Deploy Manually**
   ```bash
   # Create data directory
   mkdir -p data
   
   # Build and start
   docker-compose up -d --build
   ```

4. **Verify Deployment**
   ```bash
   # Check if container is running
   docker ps
   
   # View logs
   docker-compose logs -f
   ```
   
   Press Ctrl+C to exit logs

### Step 6: Access Your Application

1. **Open in Browser**
   ```
   http://YOUR_INSTANCE_IP:8501
   ```
   
   Example: `http://54.123.45.67:8501`

2. **Test the Application**
   - Enter a stock symbol (e.g., AAPL, TSLA)
   - Click "Analyze"
   - Analysis should complete in 25-30 seconds

---

## Management Commands

### View Logs
```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service logs
docker logs stock-market-ai-agent
```

### Restart Application
```bash
# Restart container
docker-compose restart

# Stop and start
docker-compose down
docker-compose up -d
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Stop Application
```bash
docker-compose down
```

### Check Resource Usage
```bash
# Container stats
docker stats

# System resources
htop  # Install with: sudo apt-get install htop
```

---

## Troubleshooting

### Container Won't Start

1. **Check logs**:
   ```bash
   docker-compose logs
   ```

2. **Verify .env file**:
   ```bash
   cat .env
   ```

3. **Check port availability**:
   ```bash
   sudo netstat -tulpn | grep 8501
   ```

4. **Rebuild from scratch**:
   ```bash
   docker-compose down
   docker system prune -a
   docker-compose up -d --build
   ```

### Can't Access from Browser

1. **Verify firewall rule** in Lightsail console (port 8501)

2. **Check if container is running**:
   ```bash
   docker ps
   ```

3. **Test locally on server**:
   ```bash
   curl http://localhost:8501
   ```

4. **Check Lightsail instance status** in console

### Slow Performance

1. **Check resource usage**:
   ```bash
   docker stats
   htop
   ```

2. **Upgrade instance** if needed:
   - Go to Lightsail console
   - Click instance → "Manage" → "Snapshots"
   - Create snapshot
   - Create new instance from snapshot with larger plan

3. **Check API rate limits** in logs

### Out of Memory

1. **Upgrade to $20/month plan** (4GB RAM)

2. **Add swap space**:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

---

## Security Best Practices

### 1. Secure SSH Access

```bash
# Disable password authentication
sudo nano /etc/ssh/sshd_config

# Set: PasswordAuthentication no
# Restart SSH
sudo systemctl restart sshd
```

### 2. Enable Automatic Updates

```bash
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. Set Up Firewall (UFW)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8501/tcp
sudo ufw enable
```

### 4. Regular Backups

1. **Create Snapshot** in Lightsail console:
   - Go to instance → "Snapshots" tab
   - Click "Create snapshot"
   - Name it with date (e.g., `stock-agent-2025-01-25`)

2. **Automate Snapshots**:
   - Enable automatic snapshots in Lightsail console
   - Set retention period (7 days recommended)

---

## Cost Optimization

### Current Costs
- **Lightsail Instance**: $10/month
- **Data Transfer**: Included (3TB/month)
- **Static IP**: Free (while attached to instance)
- **Snapshots**: $0.05/GB/month (optional)

### Total Monthly Cost: ~$10-12

### Tips to Reduce Costs
1. Delete unused snapshots
2. Stop instance when not in use (you'll still pay for storage)
3. Use smaller instance if traffic is low
4. Monitor data transfer usage

---

## Optional Enhancements

### 1. Set Up Custom Domain

1. **Register Domain** (e.g., GoDaddy, Namecheap)

2. **Create DNS A Record**:
   - Point to your Lightsail static IP
   - Example: `stocks.yourdomain.com → 54.123.45.67`

3. **Wait for DNS Propagation** (5-30 minutes)

4. **Access via Domain**:
   ```
   http://stocks.yourdomain.com:8501
   ```

### 2. Enable HTTPS with SSL

1. **Install Nginx**:
   ```bash
   sudo apt-get install nginx certbot python3-certbot-nginx
   ```

2. **Configure Nginx**:
   ```bash
   sudo nano /etc/nginx/sites-available/stock-agent
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name stocks.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
   
   Enable site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/stock-agent /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

3. **Get SSL Certificate**:
   ```bash
   sudo certbot --nginx -d stocks.yourdomain.com
   ```

4. **Update Lightsail Firewall**:
   - Add rule for port 443 (HTTPS)
   - Add rule for port 80 (HTTP)

5. **Access via HTTPS**:
   ```
   https://stocks.yourdomain.com
   ```

### 3. Set Up Monitoring

1. **Enable CloudWatch Metrics** in Lightsail console

2. **Create Alarms**:
   - CPU > 80%
   - Network out > 2.5TB
   - Disk usage > 80%

3. **Set Up Email Notifications**

---

## Maintenance Schedule

### Daily
- Check application is accessible
- Monitor logs for errors

### Weekly
- Review resource usage
- Check for application updates
- Review API usage/costs

### Monthly
- Create manual snapshot
- Review and delete old snapshots
- Update system packages:
  ```bash
  sudo apt-get update && sudo apt-get upgrade -y
  docker-compose pull
  docker-compose up -d
  ```

---

## Support & Resources

### Documentation
- Lightsail Docs: https://lightsail.aws.amazon.com/ls/docs
- Docker Docs: https://docs.docker.com/
- Streamlit Docs: https://docs.streamlit.io/

### Common Issues
- Check GitHub Issues for known problems
- Review application logs first
- Test locally with Docker before deploying

### Getting Help
1. Check logs: `docker-compose logs`
2. Review this guide's troubleshooting section
3. Search GitHub issues
4. Create new issue with logs and error details

---

## Conclusion

Your Stock Market AI Agent is now deployed on AWS Lightsail with:
- ✅ Fast 25-30 second response times
- ✅ No cold starts
- ✅ Always-on availability
- ✅ $10/month cost
- ✅ Easy management and updates

Access your application at: `http://YOUR_INSTANCE_IP:8501`

Happy analyzing! 📈
