# Deployment Quick Reference

One-page reference for deploying and managing the Stock Market AI Agent on AWS Lightsail.

## 🚀 Quick Deploy (5-7 minutes with AWS CLI)

### Option 1: AWS CLI (Automated - Fastest)
```bash
# From your local machine
./deploy-aws-cli.sh
# Follow prompts - done in 5-7 minutes!
```

### Option 2: Manual Deployment (15 minutes)

### 1. Create Lightsail Instance
```
AWS Console → Lightsail → Create Instance
• Platform: Ubuntu 22.04 LTS
• Plan: $10/month (2GB RAM)
• Name: stock-market-ai-agent
```

### 2. Configure Firewall
```
Instance → Networking → Add Rule
• Port: 8501
• Protocol: TCP
• Source: Anywhere
```

### 3. Deploy Application
```bash
# SSH into instance
ssh ubuntu@YOUR_IP

# Run deployment
git clone <repo-url>
cd stock-market-ai-agent
cp .env.example .env
nano .env  # Add API keys
./deploy.sh
```

### 4. Access Application
```
http://YOUR_IP:8501
```

---

## 📋 Essential Commands

### Container Management
```bash
# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Start
docker-compose up -d

# Rebuild
docker-compose up -d --build
```

### System Monitoring
```bash
# Container status
docker ps

# Resource usage
docker stats

# System resources
htop

# Disk usage
df -h
```

### Updates
```bash
# Update code
git pull
docker-compose up -d --build

# Update system
sudo apt-get update && sudo apt-get upgrade -y
```

---

## 🔧 Troubleshooting

### Container Won't Start
```bash
docker-compose logs
docker-compose down
docker-compose up -d --build
```

### Can't Access Application
1. Check firewall (port 8501)
2. Verify container: `docker ps`
3. Test locally: `curl http://localhost:8501`

### Slow Performance
```bash
docker stats  # Check resources
docker-compose logs  # Check errors
```

### Out of Memory
- Upgrade to $20/month plan (4GB RAM)
- Add swap space (see full guide)

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Response Time | 25-30 seconds |
| Cold Start | None (always-on) |
| Memory Usage | 1.2-1.5 GB |
| CPU Usage | 60-80% during analysis |
| Disk Usage | ~2 GB |
| Monthly Cost | $10-12 |

---

## 🔐 Security Checklist

- [ ] Firewall configured (port 8501 only)
- [ ] SSH key-based authentication
- [ ] `.env` file permissions: `chmod 600 .env`
- [ ] API keys not in git
- [ ] Regular snapshots enabled
- [ ] System updates automated

---

## 📅 Maintenance Schedule

### Daily
- Check application accessibility
- Review logs for errors

### Weekly
- Check resource usage
- Review API usage

### Monthly
- Create snapshot
- Update system packages
- Update application
- Delete old snapshots

---

## 🆘 Emergency Procedures

### Application Down
```bash
# Quick restart
docker-compose restart

# Full restart
docker-compose down
docker-compose up -d
```

### Rollback to Previous Version
```bash
# Via snapshot
# Lightsail Console → Snapshots → Create instance

# Via git
git checkout <previous-commit>
docker-compose up -d --build
```

### Complete Rebuild
```bash
docker-compose down
docker system prune -a
docker-compose up -d --build
```

---

## 📞 Support Resources

| Resource | Link |
|----------|------|
| Full Deployment Guide | [LIGHTSAIL_DEPLOYMENT.md](LIGHTSAIL_DEPLOYMENT.md) |
| Docker Quick Start | [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) |
| Architecture Diagram | [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) |
| Deployment Checklist | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) |
| Application Docs | [README.md](README.md) |

---

## 💡 Quick Tips

1. **Always test locally first**: `docker-compose up -d --build`
2. **Create snapshots before changes**: Lightsail Console → Snapshots
3. **Monitor resource usage**: `docker stats` and `htop`
4. **Check logs regularly**: `docker-compose logs -f`
5. **Keep system updated**: `sudo apt-get update && upgrade`

---

## 📝 Instance Information Template

```
Instance IP:     ___.___.___.___ 
Access URL:      http://___.___.___.___ :8501
Instance ID:     _______________
Region:          _______________
Created:         _______________
Last Snapshot:   _______________
```

---

## 🎯 Success Criteria

Deployment is successful when:
- ✅ Application accessible via IP
- ✅ Analysis completes in 25-30 seconds
- ✅ All features working
- ✅ No critical errors in logs
- ✅ First snapshot created

---

**Need detailed help?** See [LIGHTSAIL_DEPLOYMENT.md](LIGHTSAIL_DEPLOYMENT.md)

**Ready to deploy?** Follow the Quick Deploy steps above! 🚀
