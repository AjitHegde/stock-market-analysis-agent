# Authentication Guide

Complete guide for securing your Stock Market AI Agent with username/password authentication.

## Overview

The web UI now includes built-in authentication to protect your application from unauthorized access.

### Features

- ✅ Username/password authentication
- ✅ Secure password hashing (SHA-256)
- ✅ Session management
- ✅ Logout functionality
- ✅ Environment-based configuration
- ✅ Default credentials for quick setup

## Quick Setup

### 1. Default Credentials (Development)

The application comes with default credentials for quick testing:

- **Username**: `admin`
- **Password**: `changeme`

⚠️ **Warning**: Change these credentials before deploying to production!

### 2. Custom Credentials

Edit your `.env` file:

```bash
# Authentication
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_secure_password
```

### 3. Restart Application

```bash
# Local Docker
docker-compose restart

# AWS Lightsail
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP
cd ~/stock-market-ai-agent
sudo docker-compose restart
```

## Security Best Practices

### Use Strong Passwords

Generate a strong password:

```bash
# macOS/Linux
openssl rand -base64 32

# Or use a password manager
```

### Use Password Hashing (Recommended)

Instead of storing plain passwords, use pre-hashed passwords:

**Step 1: Generate password hash**

```bash
python src/auth.py "your_secure_password"
```

Output:
```
Password hash for 'your_secure_password':
5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8

Add this to your .env file:
AUTH_PASSWORD_HASH=5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
```

**Step 2: Update .env file**

```bash
# Use hash instead of plain password
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8

# Remove or comment out AUTH_PASSWORD
# AUTH_PASSWORD=changeme
```

**Step 3: Restart application**

```bash
docker-compose restart
```

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AUTH_USERNAME` | Username for login | `admin` | No |
| `AUTH_PASSWORD` | Plain text password | `changeme` | No* |
| `AUTH_PASSWORD_HASH` | SHA-256 hash of password | None | No* |

*Either `AUTH_PASSWORD` or `AUTH_PASSWORD_HASH` must be set.

### Priority

If both `AUTH_PASSWORD` and `AUTH_PASSWORD_HASH` are set:
- `AUTH_PASSWORD_HASH` takes priority
- `AUTH_PASSWORD` is ignored

## Usage

### Login

1. Open application URL: `http://YOUR_IP:8501`
2. Enter username and password
3. Click "Login"
4. Access granted!

### Logout

1. Click "🚪 Logout" button in sidebar
2. Redirected to login page

### Session Management

- Sessions persist until logout or browser close
- No automatic timeout (always-on session)
- Each browser/device requires separate login

## Deployment

### Local Testing

```bash
# Update .env with credentials
nano .env

# Restart Docker
docker-compose restart

# Test login at http://localhost:8501
```

### AWS Lightsail Deployment

**Option 1: Update .env and redeploy**

```bash
# 1. Update local .env file with new credentials
nano .env

# 2. Create deployment package
tar -czf /tmp/deployment.tar.gz -C . src requirements.txt Dockerfile docker-compose.yml .dockerignore run_web_ui.sh deploy.sh .env

# 3. Upload to instance
scp -i ~/.ssh/stock-agent-key.pem /tmp/deployment.tar.gz ubuntu@YOUR_IP:~/

# 4. SSH and redeploy
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP
cd ~/stock-market-ai-agent
tar -xzf ~/deployment.tar.gz
sudo docker-compose up -d --build
```

**Option 2: Update credentials directly on instance**

```bash
# SSH into instance
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP

# Edit .env file
cd ~/stock-market-ai-agent
nano .env

# Update credentials:
# AUTH_USERNAME=your_username
# AUTH_PASSWORD=your_secure_password

# Restart application
sudo docker-compose restart
```

## Troubleshooting

### Can't Login with Default Credentials

**Check environment variables:**

```bash
# SSH into instance
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP

# Check .env file
cd ~/stock-market-ai-agent
cat .env | grep AUTH

# Should show:
# AUTH_USERNAME=admin
# AUTH_PASSWORD=changeme
```

**Restart container:**

```bash
sudo docker-compose restart
```

### Forgot Password

**Reset to default:**

```bash
# SSH into instance
ssh -i ~/.ssh/stock-agent-key.pem ubuntu@YOUR_IP

# Edit .env
cd ~/stock-market-ai-agent
nano .env

# Set to defaults:
AUTH_USERNAME=admin
AUTH_PASSWORD=changeme

# Restart
sudo docker-compose restart
```

### Login Page Not Showing

**Check if authentication is enabled:**

```bash
# View container logs
sudo docker-compose logs | grep -i auth

# Should see authentication module loading
```

**Verify auth.py exists:**

```bash
ls -l src/auth.py
```

### Session Expired

- Close browser and reopen
- Clear browser cache
- Try incognito/private mode

## Advanced Configuration

### Multiple Users (Future Enhancement)

Currently supports single user. For multiple users, consider:

1. **Nginx Basic Auth**: Add Nginx reverse proxy with basic auth
2. **OAuth Integration**: Integrate with Google/GitHub OAuth
3. **Database Backend**: Store users in database

### IP Whitelisting

Restrict access to specific IPs using Lightsail firewall:

```bash
# Allow only your IP
aws lightsail put-instance-public-ports \
  --instance-name stock-market-ai-agent \
  --port-infos '[
    {"fromPort":22,"toPort":22,"protocol":"tcp","cidrs":["YOUR_IP/32"]},
    {"fromPort":8501,"toPort":8501,"protocol":"tcp","cidrs":["YOUR_IP/32"]}
  ]' \
  --region us-east-1
```

### HTTPS with SSL

For production, enable HTTPS:

1. Set up custom domain
2. Install Nginx reverse proxy
3. Get SSL certificate with Let's Encrypt
4. Configure HTTPS redirect

See [LIGHTSAIL_DEPLOYMENT.md](LIGHTSAIL_DEPLOYMENT.md) for SSL setup guide.

## Security Checklist

Before deploying to production:

- [ ] Changed default username
- [ ] Changed default password
- [ ] Using strong password (16+ characters)
- [ ] Using password hash instead of plain text
- [ ] .env file not committed to git
- [ ] .env file permissions set to 600
- [ ] Tested login/logout functionality
- [ ] Documented credentials securely
- [ ] Considered IP whitelisting
- [ ] Considered HTTPS setup

## Example Configurations

### Development (Default)

```bash
AUTH_USERNAME=admin
AUTH_PASSWORD=changeme
```

### Production (Plain Password)

```bash
AUTH_USERNAME=stockadmin
AUTH_PASSWORD=MyS3cur3P@ssw0rd!2025
```

### Production (Hashed Password - Recommended)

```bash
AUTH_USERNAME=stockadmin
AUTH_PASSWORD_HASH=5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8
```

## Testing

### Test Login

1. Open `http://YOUR_IP:8501`
2. Should see login page
3. Enter credentials
4. Should redirect to main app

### Test Logout

1. Click "🚪 Logout" in sidebar
2. Should redirect to login page
3. Try accessing app without login
4. Should show login page

### Test Invalid Credentials

1. Enter wrong username/password
2. Should show error message
3. Should not grant access

## Support

For issues or questions:

1. Check logs: `sudo docker-compose logs | grep -i auth`
2. Verify .env file: `cat .env | grep AUTH`
3. Test password hash: `python src/auth.py "your_password"`
4. Review this guide

---

## Summary

✅ **Authentication Enabled!**

Your Stock Market AI Agent is now protected with:
- Username/password authentication
- Secure password hashing
- Session management
- Logout functionality

**Default Credentials** (change in production):
- Username: `admin`
- Password: `changeme`

**Remember**: Always use strong passwords and consider HTTPS for production deployments!
