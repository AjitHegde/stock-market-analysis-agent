# Streamlit Cloud Deployment - Step by Step

**The easiest way to deploy your Stock Market AI Agent!**

## Why Streamlit Cloud?

✅ **100% Free** - No credit card required
✅ **2-minute setup** - Just connect and deploy
✅ **Auto-deploys** - Push to GitHub = automatic update
✅ **Built for Streamlit** - Perfect compatibility
✅ **Automatic HTTPS** - Secure by default
✅ **Easy secrets management** - Simple UI for API keys

## Prerequisites

- ✅ GitHub account (you have this!)
- ✅ Repository pushed to GitHub (done!)
- ✅ Streamlit app (you have this!)

## Step-by-Step Deployment

### Step 1: Go to Streamlit Cloud

Open your browser and visit:
**https://share.streamlit.io/**

### Step 2: Sign In with GitHub

1. Click **"Sign in with GitHub"**
2. Authorize Streamlit Cloud to access your repositories
3. You'll be redirected to your Streamlit Cloud dashboard

### Step 3: Create New App

1. Click the **"New app"** button (top right)
2. You'll see a form with three fields:

   **Repository:**
   ```
   AjitHegde/stock-market-analysis-agent
   ```

   **Branch:**
   ```
   main
   ```

   **Main file path:**
   ```
   src/web_ui.py
   ```

3. Click **"Deploy!"**

### Step 4: Wait for Deployment

- First deployment takes 2-5 minutes
- You'll see a progress indicator
- The app will automatically start once ready

### Step 5: Add Secrets (Environment Variables)

**IMPORTANT:** Your app needs authentication credentials!

1. While the app is deploying (or after), click on **"Settings"** (bottom left)
2. Go to **"Secrets"** section
3. Add your secrets in **TOML format**:

```toml
# Authentication (Required)
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "1212apap1212"

# API Keys (Optional - add if you have them)
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_key_here"
FINNHUB_API_KEY = "your_finnhub_key_here"
NEWS_API_KEY = "your_news_api_key_here"
```

4. Click **"Save"**
5. The app will automatically restart with the new secrets

### Step 6: Access Your App

Your app will be live at a URL like:
```
https://ajithegde-stock-market-analysis-agent-srcweb-ui-xxxxx.streamlit.app
```

The exact URL will be shown in your Streamlit Cloud dashboard.

### Step 7: Test Your App

1. Open the URL in your browser
2. You should see the login page
3. Login with:
   - Username: `admin`
   - Password: `1212apap1212`
4. Try analyzing a stock (e.g., AAPL, TSLA)

## Managing Your App

### View Logs

1. Go to your Streamlit Cloud dashboard
2. Click on your app
3. Click **"Manage app"** → **"Logs"**
4. You'll see real-time logs

### Update Your App

**Automatic Updates:**
- Just push changes to GitHub
- Streamlit Cloud will automatically redeploy
- No manual action needed!

**Manual Reboot:**
1. Go to app settings
2. Click **"Reboot app"**

### Change Secrets

1. Settings → Secrets
2. Edit the TOML content
3. Click Save
4. App will restart automatically

### Delete App

1. Settings → General
2. Scroll to bottom
3. Click **"Delete app"**

## Custom Domain (Optional)

### Add Your Own Domain

1. Go to **Settings** → **General**
2. Scroll to **"Custom domain"**
3. Enter your domain (e.g., `stocks.yourdomain.com`)
4. Click **"Add domain"**

### Update DNS Records

Add a CNAME record in your domain provider:
```
Type: CNAME
Name: stocks (or your subdomain)
Value: [provided by Streamlit Cloud]
TTL: 3600
```

Wait 5-60 minutes for DNS propagation.

## Troubleshooting

### App Won't Start

**Check logs:**
1. Dashboard → Your app → Manage app → Logs
2. Look for error messages

**Common issues:**
- Missing secrets (AUTH_USERNAME, AUTH_PASSWORD)
- Wrong file path (should be `src/web_ui.py`)
- Python package errors (check requirements.txt)

**Solution:**
- Add missing secrets in Settings → Secrets
- Verify file path in Settings → General
- Check requirements.txt has all dependencies

### Login Not Working

**Problem:** Can't login with credentials

**Solution:**
1. Go to Settings → Secrets
2. Verify AUTH_USERNAME and AUTH_PASSWORD are set:
   ```toml
   AUTH_USERNAME = "admin"
   AUTH_PASSWORD = "1212apap1212"
   ```
3. Save and wait for app to restart

### App is Slow

**Why:** Free tier has limited resources (1GB RAM)

**Solutions:**
1. **Accept it:** Free tier has limitations
2. **Optimize code:** Reduce memory usage
3. **Upgrade:** Contact Streamlit for paid options
4. **Alternative:** Deploy to Railway or Render for better performance

### App Goes to Sleep

**Why:** Free tier apps sleep after 7 days of inactivity

**Solution:**
- Just visit the URL to wake it up (takes ~30 seconds)
- Or use a service like UptimeRobot to ping it regularly

### Can't Find My App

**Check:**
1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. You should see your app in the dashboard

**If not there:**
- Redeploy following steps above

## API Keys (Optional)

Your app works without API keys, but for better data:

### Alpha Vantage (Stock Data)
1. Get free key: https://www.alphavantage.co/support/#api-key
2. Add to secrets:
   ```toml
   ALPHA_VANTAGE_API_KEY = "your_key"
   ```

### Finnhub (Company News)
1. Get free key: https://finnhub.io/register
2. Add to secrets:
   ```toml
   FINNHUB_API_KEY = "your_key"
   ```

### NewsAPI (News Articles)
1. Get free key: https://newsapi.org/register
2. Add to secrets:
   ```toml
   NEWS_API_KEY = "your_key"
   ```

## Sharing Your App

### Public Access

Your app is **publicly accessible** by default!

Share the URL with anyone:
```
https://ajithegde-stock-market-analysis-agent-srcweb-ui-xxxxx.streamlit.app
```

They'll need to login with your credentials:
- Username: `admin`
- Password: `1212apap1212`

### Change Password

To change the password:

1. Generate new password hash:
   ```bash
   python -c "import hashlib; print(hashlib.sha256('your_new_password'.encode()).hexdigest())"
   ```

2. Update secrets in Streamlit Cloud:
   ```toml
   AUTH_USERNAME = "admin"
   AUTH_PASSWORD = "your_new_password"
   ```

3. Save and restart

## Monitoring

### Usage Stats

Streamlit Cloud provides basic stats:
- Number of viewers
- Active sessions
- Resource usage

Access via: Dashboard → Your app → Analytics

### Uptime

Free tier apps:
- Sleep after 7 days of inactivity
- Wake up in ~30 seconds when accessed
- No uptime guarantee

## Limits (Free Tier)

- **RAM:** 1GB
- **CPU:** Shared
- **Storage:** Limited
- **Bandwidth:** Unlimited
- **Apps:** Unlimited
- **Uptime:** Apps sleep after inactivity

## Upgrade Options

Contact Streamlit for:
- More resources
- Always-on apps
- Priority support
- Custom domains
- Private apps

## Alternative Platforms

If Streamlit Cloud doesn't meet your needs:

### Railway.app ($5-10/month)
- Better performance
- Always-on
- 2GB RAM
- See: CLOUD_DEPLOYMENT_GUIDE.md

### Render.com ($7/month)
- Always-on
- 512MB RAM
- Good performance
- See: CLOUD_DEPLOYMENT_GUIDE.md

### Fly.io (Free tier)
- 3 free VMs
- Global edge
- Better performance
- See: CLOUD_DEPLOYMENT_GUIDE.md

## Summary

✅ **Deployed!** Your Stock Market AI Agent is now live!

**Your URL:**
```
https://ajithegde-stock-market-analysis-agent-srcweb-ui-xxxxx.streamlit.app
```

**Login:**
- Username: `admin`
- Password: `1212apap1212`

**Features:**
- 📊 Stock Analysis
- 🔍 Stock Scanner
- 🔐 Authentication
- 📈 Real-time data

**Next Steps:**
1. Test your app
2. Share with friends
3. Add API keys for better data
4. Consider custom domain

Enjoy your deployed app! 🚀📈
