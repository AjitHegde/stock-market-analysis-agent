# 🚀 Deploy to Streamlit Community Cloud

Deploy your Stock Market AI Agent to Streamlit Community Cloud for **FREE** with automatic HTTPS and a public URL!

## Why Streamlit Cloud?

✅ **Completely FREE** - No credit card required
✅ **Direct GitHub integration** - Deploy in 2 minutes
✅ **Automatic HTTPS** - Secure by default
✅ **Custom subdomain** - Get yourapp.streamlit.app
✅ **Always-on** - No cold starts
✅ **Built for Streamlit** - Optimized performance
✅ **Easy secrets management** - Secure API key storage

## Prerequisites

- GitHub account (you already have this!)
- Your repository: https://github.com/AjitHegde/stock-market-analysis-agent
- API keys for:
  - Alpha Vantage (free at https://www.alphavantage.co/support/#api-key)
  - Finnhub (free at https://finnhub.io/register)
  - NewsAPI (free at https://newsapi.org/register)

## Step-by-Step Deployment

### Step 1: Sign Up for Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click **"Sign up"** or **"Continue with GitHub"**
3. Authorize Streamlit to access your GitHub repositories
4. You'll be redirected to your Streamlit Cloud dashboard

### Step 2: Deploy Your App

1. Click **"New app"** button in the dashboard
2. Fill in the deployment form:
   - **Repository**: `AjitHegde/stock-market-analysis-agent`
   - **Branch**: `main`
   - **Main file path**: `src/web_ui.py`
   - **App URL**: Choose your subdomain (e.g., `stock-ai-agent.streamlit.app`)

3. Click **"Advanced settings"** (optional but recommended):
   - **Python version**: `3.11` (or your current version)
   - **Requirements file**: `requirements.txt` (auto-detected)

4. Click **"Deploy!"**

### Step 3: Configure Secrets (API Keys & Credentials)

While the app is deploying (or after it fails the first time due to missing secrets):

1. In your app dashboard, click **"⚙️ Settings"** (bottom right)
2. Click **"Secrets"** in the left sidebar
3. Add your secrets in TOML format:

```toml
# Authentication
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "your-secure-password-here"

# API Keys
ALPHA_VANTAGE_API_KEY = "your-alpha-vantage-key"
FINNHUB_API_KEY = "your-finnhub-key"
NEWS_API_KEY = "your-newsapi-key"

# Optional (if you have them)
REDDIT_API_KEY = "your-reddit-key"
TWITTER_API_KEY = "your-twitter-key"
```

4. Click **"Save"**
5. The app will automatically restart with the new secrets

### Step 4: Access Your App

Your app will be available at:
```
https://your-chosen-name.streamlit.app
```

For example:
```
https://stock-ai-agent.streamlit.app
```

## Configuration Notes

### Environment Variables vs Secrets

Streamlit Cloud uses `st.secrets` to access environment variables. Your app already supports both methods:

```python
# In your code, this works automatically:
api_key = os.getenv('ALPHA_VANTAGE_API_KEY')  # Falls back to st.secrets
```

### Authentication

Your authentication system works perfectly on Streamlit Cloud:
- Username/password are stored securely in secrets
- SHA-256 password hashing is used
- Session state persists across page reloads

### Resource Limits (Free Tier)

- **CPU**: 1 vCPU (shared)
- **Memory**: 1 GB RAM
- **Storage**: Limited (no persistent storage)
- **Uptime**: Always-on (sleeps after 7 days of inactivity)
- **Bandwidth**: Unlimited

**Note**: If your app sleeps due to inactivity, it will wake up automatically when someone visits the URL (takes ~30 seconds).

## Updating Your App

### Automatic Updates

Streamlit Cloud automatically redeploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "feat: Add new feature"
git push origin main

# App automatically redeploys in ~2 minutes!
```

### Manual Reboot

If needed, you can manually reboot from the dashboard:
1. Go to your app dashboard
2. Click **"⋮"** (three dots menu)
3. Click **"Reboot app"**

## Custom Domain (Optional)

Want to use your own domain instead of `.streamlit.app`?

1. Upgrade to Streamlit Cloud Teams ($250/month)
2. Or use a reverse proxy with your own server

For most users, the free `.streamlit.app` domain is perfect!

## Monitoring & Logs

### View Logs

1. Go to your app dashboard
2. Click **"Manage app"** at the bottom right
3. Click **"Logs"** to see real-time application logs

### Monitor Usage

Streamlit Cloud provides basic analytics:
- Number of viewers
- App uptime
- Resource usage

## Troubleshooting

### App Won't Start

**Problem**: App shows error on startup

**Solutions**:
1. Check logs for specific error messages
2. Verify all required secrets are configured
3. Ensure `requirements.txt` has all dependencies
4. Check Python version compatibility

### API Rate Limits

**Problem**: "API rate limit exceeded" errors

**Solutions**:
1. Alpha Vantage free tier: 5 requests/minute, 500/day
2. Consider upgrading API plans for production use
3. Implement caching (already done in the app)

### Memory Issues

**Problem**: App crashes with "Out of memory"

**Solutions**:
1. Free tier has 1GB RAM limit
2. Optimize data loading and caching
3. Consider upgrading to Streamlit Cloud Teams (more resources)

### App Sleeping

**Problem**: App takes 30 seconds to load after inactivity

**Solutions**:
1. This is normal for free tier (sleeps after 7 days)
2. Upgrade to Teams plan for always-on apps
3. Or use a simple uptime monitor to ping your app periodically

## Security Best Practices

### ✅ DO:
- Store API keys in Streamlit Cloud secrets (never in code)
- Use strong passwords for authentication
- Keep your GitHub repository private if it contains sensitive data
- Regularly update dependencies

### ❌ DON'T:
- Commit `.env` or `secrets.toml` files with real credentials
- Share your secrets publicly
- Use default passwords in production
- Expose internal API endpoints

## Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Streamlit Cloud** | ✅ FREE | $250/mo (Teams) | Streamlit apps |
| AWS Lightsail | $10/mo | $10-$160/mo | Full control |
| Render.com | ✅ FREE | $7/mo | Docker apps |
| Railway.app | $5 credit | $5/mo | Quick deploys |
| Heroku | ❌ No free | $7/mo | Legacy apps |

## Next Steps

### 1. Get API Keys

If you don't have them yet:

**Alpha Vantage** (Stock data):
- Sign up: https://www.alphavantage.co/support/#api-key
- Free tier: 5 requests/min, 500/day
- Instant approval

**Finnhub** (Company news):
- Sign up: https://finnhub.io/register
- Free tier: 60 requests/min
- Instant approval

**NewsAPI** (News articles):
- Sign up: https://newsapi.org/register
- Free tier: 100 requests/day
- Instant approval

### 2. Deploy to Streamlit Cloud

Follow the steps above to deploy your app!

### 3. Share Your App

Once deployed, share your app URL:
```
https://your-app-name.streamlit.app
```

### 4. Monitor & Improve

- Check logs regularly
- Monitor API usage
- Gather user feedback
- Add new features

## Example Deployment

Here's what a successful deployment looks like:

```
✅ Repository: AjitHegde/stock-market-analysis-agent
✅ Branch: main
✅ Main file: src/web_ui.py
✅ Python: 3.11
✅ Secrets: Configured (5 secrets)
✅ Status: Running
✅ URL: https://stock-ai-agent.streamlit.app
```

## Support

### Streamlit Cloud Support
- Documentation: https://docs.streamlit.io/streamlit-community-cloud
- Community Forum: https://discuss.streamlit.io/
- GitHub Issues: https://github.com/streamlit/streamlit/issues

### Your App Support
- GitHub: https://github.com/AjitHegde/stock-market-analysis-agent
- Issues: https://github.com/AjitHegde/stock-market-analysis-agent/issues

## Summary

🎉 **Streamlit Cloud is the perfect choice for your Stock Market AI Agent!**

**Advantages:**
- ✅ Completely free
- ✅ 2-minute setup
- ✅ Automatic HTTPS
- ✅ GitHub integration
- ✅ Built for Streamlit
- ✅ No server management

**Your app will be live at:**
```
https://your-chosen-name.streamlit.app
```

**Ready to deploy?** Go to https://share.streamlit.io/ and click "New app"!

---

**Need help?** Check the troubleshooting section or open an issue on GitHub.

Happy deploying! 🚀📈
