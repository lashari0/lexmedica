# Deployment Guide

This guide covers deploying MR-KA to free hosting platforms.

## Overview

- **Backend**: Render (free tier) or Railway
- **Frontend**: Vercel (free tier)
- **Vector DB**: ChromaDB (embedded in backend)
- **LLM**: Hugging Face Inference API (free tier) or Ollama (self-hosted)

## Backend Deployment (Render)

### Step 1: Prepare Repository

Ensure your code is pushed to GitHub.

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Verify your email

### Step 3: Create Web Service

1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `mr-ka-backend`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 4: Environment Variables

Add these in Render dashboard:

```
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=your_key_here
HUGGINGFACE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
CHROMA_PERSIST_DIR=/opt/render/project/src/chroma_db
UPLOAD_DIR=/opt/render/project/src/uploads
ALLOWED_ORIGINS=https://your-frontend.vercel.app
TOP_K=5
SIMILARITY_THRESHOLD=0.7
```

### Step 5: Deploy

1. Click "Create Web Service"
2. Wait for deployment (first deploy takes ~5-10 minutes)
3. Note your backend URL (e.g., `https://mr-ka-backend.onrender.com`)

### Important Notes

- Render free tier sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake
- Persistent disk is available for ChromaDB storage
- Consider upgrading if you need always-on service

## Frontend Deployment (Vercel)

### Step 1: Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Import your repository

### Step 2: Configure Project

1. **Framework Preset**: Next.js
2. **Root Directory**: `frontend`
3. **Build Command**: `npm run build` (default)
4. **Output Directory**: `.next` (default)

### Step 3: Environment Variables

Add in Vercel dashboard:

```
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

### Step 4: Deploy

1. Click "Deploy"
2. Wait for build (~2-3 minutes)
3. Your app will be live at `https://your-project.vercel.app`

## Alternative: Railway Deployment

Railway offers better free tier with no sleep:

### Backend on Railway

1. Go to [railway.app](https://railway.app)
2. Create new project from GitHub
3. Add Python service
4. Set root to `backend`
5. Railway auto-detects FastAPI and deploys
6. Add environment variables (same as Render)

### Frontend on Railway

1. Add another service to same project
2. Select Node.js
3. Set root to `frontend`
4. Railway auto-detects Next.js
5. Add environment variable: `NEXT_PUBLIC_API_URL`

## Post-Deployment Checklist

- [ ] Backend health check works: `https://your-backend.onrender.com/api/health`
- [ ] Frontend loads correctly
- [ ] CORS is configured (frontend can call backend)
- [ ] Document upload works
- [ ] Query endpoint works
- [ ] LLM API key is valid (if using Hugging Face)

## Troubleshooting

### Backend Issues

**Problem**: Service won't start
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure requirements.txt is correct

**Problem**: ChromaDB not persisting
- Verify `CHROMA_PERSIST_DIR` is set
- Check disk space in Render dashboard

**Problem**: LLM errors
- Verify API key is correct
- Check Hugging Face model name
- Ensure Ollama is running (if using local)

### Frontend Issues

**Problem**: Can't connect to backend
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS settings in backend
- Ensure backend is running

**Problem**: Build fails
- Check Node.js version (should be 18+)
- Verify all dependencies in package.json
- Check build logs in Vercel

## Monitoring

### Render

- View logs in dashboard
- Monitor uptime
- Check resource usage

### Vercel

- View deployment logs
- Monitor analytics
- Check function execution times

## Cost Optimization

1. **Use Hugging Face free tier**: 1000 requests/month
2. **Cache query results**: Reduce LLM calls
3. **Optimize Docker images**: Smaller = faster deploys
4. **Use CDN**: Vercel provides this automatically

## Scaling

When you outgrow free tiers:

1. **Backend**: Upgrade Render plan or move to Railway paid
2. **Frontend**: Vercel Pro (if needed)
3. **LLM**: Use cheaper models or self-host Ollama
4. **Vector DB**: Consider managed ChromaDB or Qdrant Cloud

## Security

- Never commit `.env` files
- Use environment variables for secrets
- Enable HTTPS (automatic on Render/Vercel)
- Set proper CORS origins
- Rate limit API endpoints (future enhancement)
