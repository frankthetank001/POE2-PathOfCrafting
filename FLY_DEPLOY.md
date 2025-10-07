# Fly.io Deployment Guide

## Prerequisites

1. **Install Fly.io CLI** (PowerShell on Windows):
   ```powershell
   pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```
   Restart terminal after installation.

2. **Login to Fly.io**:
   ```bash
   fly auth login
   ```
   Sign up if you don't have an account (free tier available).

---

## Deploy Backend

```bash
cd backend

# Create app and volume
fly launch --no-deploy --name poe2-pathofcrafting-backend
fly volumes create backend_data --size 1 --region ord

# Deploy from GHCR image
fly deploy --ha=false
```

**Your backend will be at**: `https://poe2-pathofcrafting-backend.fly.dev`

---

## Deploy Frontend

```bash
cd ../frontend

# Create app
fly launch --no-deploy --name poe2-pathofcrafting-frontend

# Deploy from GHCR image
fly deploy --ha=false
```

**Your frontend will be at**: `https://poe2-pathofcrafting-frontend.fly.dev`

---

## Configure Frontend to Connect to Backend

The frontend needs to know your backend URL. You have two options:

### Option A: Environment Variable (Recommended)

Edit `frontend/fly.toml` and add:

```toml
[env]
  API_BASE_URL = "https://poe2-pathofcrafting-backend.fly.dev"
```

Then rebuild the frontend:
```bash
cd frontend
fly deploy
```

### Option B: Custom config.js

1. Create `frontend/config.production.js`:
   ```javascript
   window.APP_CONFIG = {
     API_BASE_URL: 'https://poe2-pathofcrafting-backend.fly.dev'
   }
   ```

2. Update `frontend/fly.toml` to mount it:
   ```toml
   [mounts]
     source = "config_override"
     destination = "/usr/share/nginx/html/config.js"
   ```

---

## Verify Deployment

```bash
# Check backend health
curl https://poe2-pathofcrafting-backend.fly.dev/health

# Check frontend
curl https://poe2-pathofcrafting-frontend.fly.dev

# View logs
fly logs -a poe2-pathofcrafting-backend
fly logs -a poe2-pathofcrafting-frontend
```

---

## Update App (After Pushing New Images)

```bash
# Backend
cd backend
fly deploy

# Frontend
cd frontend
fly deploy
```

Fly.io will automatically pull the latest `:latest` tag from GHCR.

---

## Costs

- **Backend**: ~$5-7/month (512MB RAM + 1GB volume)
- **Frontend**: ~$2-3/month (256MB RAM)
- **Total**: ~$7-10/month

Free tier includes:
- Up to 3 shared-cpu-1x VMs
- 3GB persistent volume storage
- 160GB outbound data transfer

---

## Troubleshooting

### Backend database not initializing

Check logs:
```bash
fly logs -a poe2-pathofcrafting-backend
```

Volume should mount at `/app/data`. The entrypoint script will auto-initialize on first run.

### Frontend can't reach backend (CORS)

Your backend is already configured for `cors_origins: ["*"]`, so this should work. If not:

```bash
fly ssh console -a poe2-pathofcrafting-backend
cat /app/data/crafting.db  # Check if DB exists
```

### Want to use custom domain?

```bash
# Add your domain
fly certs add yourdomain.com -a poe2-pathofcrafting-frontend

# Update DNS
# Add CNAME: yourdomain.com → poe2-pathofcrafting-frontend.fly.dev
```

---

## Commands Reference

```bash
# View all apps
fly apps list

# View app info
fly info -a poe2-pathofcrafting-backend

# Scale resources
fly scale memory 1024 -a poe2-pathofcrafting-backend

# SSH into container
fly ssh console -a poe2-pathofcrafting-backend

# View volumes
fly volumes list -a poe2-pathofcrafting-backend

# Destroy app (careful!)
fly apps destroy poe2-pathofcrafting-backend
```
