# Cloud Deployment Guide - Public Access

Deploy your Stock Market AI Agent to public cloud platforms without AWS credentials.

## Quick Comparison

| Platform | Cost | Setup Time | Custom Domain | HTTPS | Best For |
|----------|------|------------|---------------|-------|----------|
| **Streamlit Cloud** | Free | 2 min | ✅ | ✅ | Streamlit apps (Easiest!) |
| **Render.com** | Free tier | 5 min | ✅ | ✅ | Docker apps |
| **Railway.app** | $5 credit | 3 min | ✅ | ✅ | Quick deploys |
| **Fly.io** | Free tier | 10 min | ✅ | ✅ | Global edge |
| **Google Cloud Run** | Pay-per-use | 15 min | ✅ | ✅ | Enterprise |

---

## Option 1: Streamlit Cloud (RECOMMENDED - Easiest!)

**Perfect for Streamlit apps. 100% free, no credit card needed.**

### Prerequisites
- GitHub account (you already have this!)
- Your repository: https://github.com/AjitHegde/stock-market-analysis-agent

### Steps

#### 1. Go to Streamlit Cloud
Visit: https://share.streamlit.io/

#### 2. Sign in with GitHub
Click "Sign in with GitHub" and authorize Streamlit Cloud

#### 3. Deploy New App
- Click "New app"
- Repository: `AjitHegde/stock-market-analysis-agent`
- Branch: `main`
- Main file path: `src/web_ui.py`
- Click "Deploy!"

#### 4. Add Secrets (Environment Variables)
In the Streamlit Cloud dashboard:
- Click on your app
- Go to "Settings" → "Secrets"
- Add your secrets in TOML format:

```toml
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "1212apap1212"

# Optional: Add your API keys if you have them
ALPHA_VANTAGE_API_KEY = "your_key_here"
FINNHUB_API_KEY = "your_key_here"
NEWS_API_KEY = "your_key_here"
```

#### 5. Access Your App
Your app will be available at:
`https://ajithegde-stock-market-analysis-agent-srcweb-ui-xxxxx.streamlit.app`

### Custom Domain (Optional)
- Go to Settings → General
- Add your custom domain
- Update DNS records as instructed

### Pros
✅ Completely free
✅ No credit card required
✅ Automatic HTTPS
✅ Auto-deploys on git push
✅ Built specifically for Streamlit
✅ Easy secrets management

### Cons
❌ Limited to 1GB RAM (may be slow for heavy analysis)
❌ Apps sleep after inactivity (30-second cold start)

---

## Option 2: Render.com

**Great for Docker apps. Free tier available.**

### Prerequisites
- GitHub account
- Render.com account (free)

### Steps

#### 1. Create Render Account
Visit: https://render.com/
Sign up with GitHub

#### 2. Create New Web Service
- Click "New +" → "Web Service"
- Connect your GitHub repository: `AjitHegde/stock-market-analysis-agent`
- Click "Connect"

#### 3. Configure Service
- **Name**: stock-market-ai-agent
- **Region**: Oregon (US West)
- **Branch**: main
- **Runtime**: Docker
- **Instance Type**: Free

#### 4. Add Environment Variables
Click "Advanced" and add:
```
AUTH_USERNAME=admin
AUTH_PASSWORD=1212apap1212
PORT=8501
```

Add API keys if you have them:
```
ALPHA_VANTAGE_API_KEY=your_key
FINNHUB_API_KEY=your_key
NEWS_API_KEY=your_key
```

#### 5. Deploy
Click "Create Web Service"

Wait 5-10 minutes for first deployment.

#### 6. Access Your App
Your app will be at:
`https://stock-market-ai-agent.onrender.com`

### Custom Domain
- Go to Settings → Custom Domain
- Add your domain
- Update DNS with provided CNAME

### Pros
✅ Free tier available
✅ Automatic HTTPS
✅ Docker support
✅ Auto-deploys on git push
✅ Better performance than Streamlit Cloud

### Cons
❌ Free tier spins down after 15 min inactivity (cold start ~30 sec)
❌ Limited to 512MB RAM on free tier

### Upgrade to Paid ($7/month)
- Always-on (no cold starts)
- 512MB RAM
- Better performance

---

## Option 3: Railway.app

**Modern platform with great developer experience.**

### Prerequisites
- GitHub account
- Railway account (free $5 credit)

### Steps

#### 1. Create Railway Account
Visit: https://railway.app/
Sign up with GitHub

#### 2. Create New Project
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose: `AjitHegde/stock-market-analysis-agent`

#### 3. Configure Service
Railway will auto-detect the Dockerfile

#### 4. Add Environment Variables
Click on your service → Variables:
```
AUTH_USERNAME=admin
AUTH_PASSWORD=1212apap1212
PORT=8501
```

Add API keys:
```
ALPHA_VANTAGE_API_KEY=your_key
FINNHUB_API_KEY=your_key
NEWS_API_KEY=your_key
```

#### 5. Generate Domain
- Click "Settings" → "Networking"
- Click "Generate Domain"

#### 6. Access Your App
Your app will be at:
`https://stock-market-ai-agent-production.up.railway.app`

### Custom Domain
- Settings → Networking → Custom Domain
- Add your domain
- Update DNS records

### Pros
✅ $5 free credit (lasts ~1 month)
✅ No cold starts
✅ Great performance
✅ Simple setup
✅ Automatic HTTPS

### Cons
❌ Requires credit card after trial
❌ ~$5-10/month after free credit

---

## Option 4: Fly.io

**Global edge deployment with free tier.**

### Prerequisites
- Fly.io account
- Fly CLI installed

### Steps

#### 1. Install Fly CLI
```bash
# macOS
brew install flyctl

# Or use install script
curl -L https://fly.io/install.sh | sh
```

#### 2. Sign Up and Login
```bash
flyctl auth signup
# or
flyctl auth login
```

#### 3. Create fly.toml
Already created in your repo!

#### 4. Deploy
```bash
# From your project directory
flyctl launch --no-deploy

# Set secrets
flyctl secrets set AUTH_USERNAME=admin
flyctl secrets set AUTH_PASSWORD=1212apap1212

# Optional: Add API keys
flyctl secrets set ALPHA_VANTAGE_API_KEY=your_key
flyctl secrets set FINNHUB_API_KEY=your_key
flyctl secrets set NEWS_API_KEY=your_key

# Deploy
flyctl deploy
```

#### 5. Access Your App
```bash
flyctl open
```

Your app will be at:
`https://stock-market-ai-agent.fly.dev`

### Custom Domain
```bash
flyctl certs add yourdomain.com
```

### Pros
✅ Free tier (3 VMs)
✅ Global edge deployment
✅ No cold starts
✅ Great performance
✅ Custom domains

### Cons
❌ Requires CLI setup
❌ More complex than web-based platforms

---

## Option 5: Google Cloud Run

**Serverless container platform. Pay only for what you use.**

### Prerequisites
- Google Cloud account
- gcloud CLI installed

### Steps

#### 1. Install gcloud CLI
```bash
# macOS
brew install google-cloud-sdk
```

#### 2. Initialize and Login
```bash
gcloud init
gcloud auth login
```

#### 3. Enable Cloud Run API
```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### 4. Build and Deploy
```bash
# Set project ID
export PROJECT_ID=your-project-id

# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/stock-agent

# Deploy to Cloud Run
gcloud run deploy stock-agent \
  --image gcr.io/$PROJECT_ID/stock-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AUTH_USERNAME=admin,AUTH_PASSWORD=1212apap1212 \
  --port 8501 \
  --memory 2Gi \
  --cpu 1
```

#### 5. Add API Keys (Optional)
```bash
gcloud run services update stock-agent \
  --set-env-vars ALPHA_VANTAGE_API_KEY=your_key,FINNHUB_API_KEY=your_key,NEWS_API_KEY=your_key
```

#### 6. Access Your App
The deployment will output your URL:
`https://stock-agent-xxxxx-uc.a.run.app`

### Custom Domain
```bash
gcloud run domain-mappings create --service stock-agent --domain yourdomain.com
```

### Pros
✅ Pay only for requests (very cheap)
✅ Auto-scales to zero
✅ 2 million requests free/month
✅ Enterprise-grade
✅ No cold starts with min instances

### Cons
❌ Requires Google Cloud account
❌ More complex setup
❌ Billing account required (but free tier is generous)

---

## My Recommendation

### For You: **Streamlit Cloud** 🏆

**Why?**
1. ✅ **100% Free** - No credit card needed
2. ✅ **2-minute setup** - Just connect GitHub and deploy
3. ✅ **Built for Streamlit** - Perfect for your app
4. ✅ **Auto-deploys** - Push to GitHub = automatic update
5. ✅ **Easy secrets** - Simple UI for environment variables

**Trade-off:**
- Apps sleep after inactivity (30-second wake-up)
- Limited to 1GB RAM

**If you need always-on with better performance:**
- **Railway.app** ($5-10/month) - Best developer experience
- **Render.com** ($7/month) - Good balance of features and price

---

## Quick Start: Streamlit Cloud (5 Minutes)

1. **Go to**: https://share.streamlit.io/
2. **Sign in** with GitHub
3. **Click** "New app"
4. **Select**:
   - Repository: `AjitHegde/stock-market-analysis-agent`
   - Branch: `main`
   - Main file: `src/web_ui.py`
5. **Add secrets** (Settings → Secrets):
   ```toml
   AUTH_USERNAME = "admin"
   AUTH_PASSWORD = "1212apap1212"
   ```
6. **Deploy!**

Your app will be live at:
`https://ajithegde-stock-market-analysis-agent-srcweb-ui-xxxxx.streamlit.app`

---

## Cost Comparison (Monthly)

| Platform | Free Tier | Paid Tier | Always-On |
|----------|-----------|-----------|-----------|
| Streamlit Cloud | ✅ Free | N/A | ❌ (sleeps) |
| Render.com | ✅ Free | $7/mo | ✅ (paid only) |
| Railway.app | $5 credit | $5-10/mo | ✅ |
| Fly.io | ✅ Free | ~$5/mo | ✅ |
| Google Cloud Run | ✅ Free tier | Pay-per-use | ✅ (with min instances) |

---

## Troubleshooting

### App Won't Start
- Check logs in platform dashboard
- Verify environment variables are set
- Ensure PORT is set to 8501

### Out of Memory
- Upgrade to paid tier
- Optimize code to use less memory
- Use Google Cloud Run (2GB RAM)

### Slow Performance
- Use paid tier for better resources
- Deploy to region closer to you
- Consider Fly.io for global edge deployment

### Authentication Not Working
- Verify AUTH_USERNAME and AUTH_PASSWORD are set
- Check secrets/environment variables in platform
- Restart the app after adding secrets

---

## Next Steps

1. **Deploy to Streamlit Cloud** (recommended)
2. **Test your app** with a few stock symbols
3. **Share the URL** with others
4. **Monitor usage** in platform dashboard
5. **Upgrade if needed** for better performance

Need help? Let me know which platform you choose!
