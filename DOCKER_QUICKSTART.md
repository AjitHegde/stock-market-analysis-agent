# Docker Quick Start Guide

Quick guide to test the Stock Market AI Agent locally with Docker before deploying to AWS Lightsail.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- API keys ready

## Quick Start (5 minutes)

### 1. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env  # or use your preferred editor
```

Add your API keys to `.env`:
```
NEWS_API_KEY=your_actual_key_here
FINNHUB_API_KEY=your_actual_key_here
ALPHA_VANTAGE_API_KEY=your_actual_key_here
```

### 2. Build and Run

```bash
# Build and start in one command
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### 3. Access Application

Open browser: http://localhost:8501

### 4. Test Analysis

- Enter a stock symbol (e.g., AAPL, TSLA)
- Click "Analyze"
- Should complete in 25-30 seconds

## Common Commands

```bash
# Stop application
docker-compose down

# Restart application
docker-compose restart

# View logs
docker-compose logs -f

# Check container status
docker ps

# Rebuild after code changes
docker-compose up -d --build

# Clean up everything
docker-compose down
docker system prune -a
```

## Troubleshooting

### Port Already in Use

If port 8501 is already in use, edit `docker-compose.yml`:
```yaml
ports:
  - "8502:8501"  # Change 8501 to 8502
```

Then access at: http://localhost:8502

### Container Exits Immediately

Check logs:
```bash
docker-compose logs
```

Common issues:
- Missing .env file
- Invalid API keys
- Port conflict

### Can't Connect to Application

1. Verify container is running:
   ```bash
   docker ps
   ```

2. Check if port is accessible:
   ```bash
   curl http://localhost:8501/_stcore/health
   ```

3. Try rebuilding:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Next Steps

Once local testing works:
1. Follow [LIGHTSAIL_DEPLOYMENT.md](LIGHTSAIL_DEPLOYMENT.md) for AWS deployment
2. Your local Docker setup is identical to production
3. Same commands work on Lightsail instance

## Performance Notes

- **First run**: 30-40 seconds (downloading models)
- **Subsequent runs**: 25-30 seconds
- **Memory usage**: ~1.5GB RAM
- **Disk usage**: ~2GB

## Development Workflow

```bash
# Make code changes
# ...

# Rebuild and test
docker-compose up -d --build

# View logs
docker-compose logs -f

# Test in browser
# http://localhost:8501

# When satisfied, deploy to Lightsail
```

## Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove all Docker data (careful!)
docker system prune -a --volumes
```

---

**Ready for production?** → See [LIGHTSAIL_DEPLOYMENT.md](LIGHTSAIL_DEPLOYMENT.md)
