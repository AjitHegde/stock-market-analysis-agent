# AWS Lightsail Deployment Checklist

Use this checklist to ensure a smooth deployment of your Stock Market AI Agent.

## Pre-Deployment

### Prerequisites
- [ ] AWS account created and verified
- [ ] Credit card added to AWS account
- [ ] API keys obtained:
  - [ ] News API key (https://newsapi.org/)
  - [ ] Finnhub API key (https://finnhub.io/)
  - [ ] Alpha Vantage API key (https://www.alphavantage.co/)
  - [ ] (Optional) Twitter API key
  - [ ] (Optional) Reddit API key

### Local Testing
- [ ] Application tested locally
- [ ] Docker installed on local machine
- [ ] `.env` file created with API keys
- [ ] Local Docker test successful:
  ```bash
  docker-compose up -d --build
  # Test at http://localhost:8501
  ```
- [ ] All features working correctly
- [ ] Stock analysis completes successfully

## AWS Lightsail Setup

### Instance Creation
- [ ] Logged into AWS Lightsail console
- [ ] Region selected (closest to you)
- [ ] Instance created:
  - [ ] Platform: Linux/Unix
  - [ ] Blueprint: Ubuntu 22.04 LTS
  - [ ] Plan: $10/month (2GB RAM, 1 vCPU, 60GB SSD)
  - [ ] Instance name: `stock-market-ai-agent`
- [ ] Instance status: Running
- [ ] Static IP noted: `___.___.___.___ `

### Firewall Configuration
- [ ] Networking tab opened
- [ ] Firewall rule added:
  - [ ] Application: Custom
  - [ ] Protocol: TCP
  - [ ] Port: 8501
  - [ ] Source: Anywhere (0.0.0.0/0)
- [ ] Rule saved and active

### SSH Access
- [ ] SSH key downloaded (if using terminal)
- [ ] Successfully connected via:
  - [ ] Browser-based SSH, OR
  - [ ] Terminal SSH with key

## Deployment

### System Setup
- [ ] System updated:
  ```bash
  sudo apt-get update
  sudo apt-get upgrade -y
  ```
- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] User added to docker group
- [ ] Logged out and back in (for group changes)
- [ ] Docker verified: `docker --version`
- [ ] Docker Compose verified: `docker-compose --version`

### Application Deployment
- [ ] Repository cloned or files uploaded
- [ ] Navigated to application directory
- [ ] `.env` file created from `.env.example`
- [ ] API keys added to `.env` file
- [ ] `.env` file verified (no placeholder values)
- [ ] Data directory created: `mkdir -p data`
- [ ] Deployment script made executable: `chmod +x deploy.sh`
- [ ] Deployment script executed: `./deploy.sh`
- [ ] Script completed without errors
- [ ] Container running: `docker ps` shows `stock-market-ai-agent`

### Verification
- [ ] Application accessible at: `http://INSTANCE_IP:8501`
- [ ] Homepage loads correctly
- [ ] Stock analysis tested (e.g., AAPL)
- [ ] Analysis completes in 25-30 seconds
- [ ] Results display correctly
- [ ] No errors in logs: `docker-compose logs`

## Post-Deployment

### Documentation
- [ ] Instance IP documented
- [ ] Access URL shared: `http://INSTANCE_IP:8501`
- [ ] API keys stored securely (password manager)
- [ ] SSH key stored securely

### Backup & Monitoring
- [ ] First snapshot created:
  - [ ] Name: `stock-agent-initial-YYYY-MM-DD`
  - [ ] Snapshot status: Available
- [ ] Automatic snapshots enabled (optional)
- [ ] CloudWatch metrics enabled (optional)
- [ ] Alerts configured (optional):
  - [ ] CPU > 80%
  - [ ] Memory > 90%
  - [ ] Disk > 80%
  - [ ] Network > 2.5TB

### Security
- [ ] SSH password authentication disabled (optional)
- [ ] UFW firewall configured (optional)
- [ ] Automatic security updates enabled (optional)
- [ ] `.env` file permissions set: `chmod 600 .env`

### Testing
- [ ] Multiple stock analyses tested
- [ ] Different stock types tested (US, Indian)
- [ ] Error handling verified
- [ ] Performance acceptable (25-30s)
- [ ] No memory issues
- [ ] Logs clean (no critical errors)

## Optional Enhancements

### Custom Domain (Optional)
- [ ] Domain registered
- [ ] DNS A record created pointing to instance IP
- [ ] DNS propagation verified
- [ ] Application accessible via domain

### SSL/HTTPS (Optional)
- [ ] Nginx installed
- [ ] Nginx configured as reverse proxy
- [ ] Certbot installed
- [ ] SSL certificate obtained
- [ ] HTTPS working
- [ ] HTTP redirects to HTTPS
- [ ] Firewall updated (ports 80, 443)

### Monitoring (Optional)
- [ ] CloudWatch agent installed
- [ ] Custom metrics configured
- [ ] Dashboard created
- [ ] Email notifications set up

## Maintenance Schedule

### Daily
- [ ] Check application accessibility
- [ ] Review logs for errors

### Weekly
- [ ] Check resource usage
- [ ] Review API usage/costs
- [ ] Check for application updates

### Monthly
- [ ] Create manual snapshot
- [ ] Update system packages
- [ ] Update application
- [ ] Review and delete old snapshots
- [ ] Review AWS bill

## Troubleshooting Checklist

If something goes wrong, check:

### Application Not Accessible
- [ ] Instance running in Lightsail console
- [ ] Firewall rule for port 8501 exists
- [ ] Container running: `docker ps`
- [ ] Logs checked: `docker-compose logs`
- [ ] Local test: `curl http://localhost:8501`

### Container Not Starting
- [ ] Logs reviewed: `docker-compose logs`
- [ ] `.env` file exists and has valid keys
- [ ] Port 8501 not in use: `sudo netstat -tulpn | grep 8501`
- [ ] Rebuild attempted: `docker-compose up -d --build`

### Slow Performance
- [ ] Resource usage checked: `docker stats`
- [ ] System resources checked: `htop`
- [ ] API rate limits checked in logs
- [ ] Instance size adequate (2GB RAM minimum)

### Out of Memory
- [ ] Upgrade to $20/month plan considered
- [ ] Swap space added (see deployment guide)
- [ ] Memory leaks investigated in logs

## Rollback Plan

If deployment fails:

### Quick Rollback
- [ ] Stop container: `docker-compose down`
- [ ] Restore from snapshot in Lightsail console
- [ ] Verify restoration successful

### Code Rollback
- [ ] Identify last working commit
- [ ] Checkout previous version: `git checkout <commit>`
- [ ] Rebuild: `docker-compose up -d --build`
- [ ] Verify working

## Success Criteria

Deployment is successful when:

- ✅ Application accessible via public IP
- ✅ Stock analysis completes in 25-30 seconds
- ✅ All features working correctly
- ✅ No critical errors in logs
- ✅ Resource usage within limits
- ✅ First snapshot created
- ✅ Documentation updated
- ✅ Access URL shared

## Support Resources

- **Deployment Guide**: [LIGHTSAIL_DEPLOYMENT.md](LIGHTSAIL_DEPLOYMENT.md)
- **Docker Guide**: [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)
- **Summary**: [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
- **Application Docs**: [README.md](README.md)

## Notes

Use this space to document instance-specific information:

```
Instance IP: ___.___.___.___ 
Instance ID: _______________
Region: _______________
Created: _______________
Access URL: http://___.___.___.___ :8501
Snapshot Schedule: _______________
```

---

**Estimated Total Time**: 15-20 minutes
**Monthly Cost**: ~$10-12
**Performance**: 25-30 seconds per analysis

Good luck with your deployment! 🚀
