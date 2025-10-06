# 🐳 Docker Guide - PoE2 PathOfCrafting

This guide explains the different Docker Compose files and how to use them.

## 📦 Docker Compose Files Overview

| File | Purpose | Use Case |
|------|---------|----------|
| `docker-compose.ghcr.yml` | **Pre-built images** | Quick start - just download and run |
| `docker-compose.yml` | **Development** | Local development with hot reload |
| `docker-compose.prod.yml` | **Production build** | Self-hosted production deployment |
| `docker-compose.example.yml` | **Documentation** | Reference with inline comments |

---

## 🚀 Quick Start (Recommended for Users)

**Just want to run the app? Use pre-built images:**

```bash
# Download the compose file
curl -O https://raw.githubusercontent.com/frankthetank001/POE2-PathOfCrafting/main/docker-compose.ghcr.yml

# Start the application
docker-compose -f docker-compose.ghcr.yml up -d

# Check status
docker-compose -f docker-compose.ghcr.yml ps

# View logs
docker-compose -f docker-compose.ghcr.yml logs -f
```

**Access the application:**
- Web UI: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Stop the application:**
```bash
docker-compose -f docker-compose.ghcr.yml down
```

---

## 🛠️ Development Setup

**Clone the repository and run locally with hot reload:**

```bash
# Clone the repository
git clone https://github.com/frankthetank001/POE2-PathOfCrafting.git
cd POE2-PathOfCrafting

# Start development environment
docker-compose up

# Or run in background
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Features:**
- ✅ Hot reload - code changes reflect immediately
- ✅ Database auto-initializes on first run
- ✅ Persistent storage via Docker volumes
- ✅ Source code mounted from host

**Access:**
- Frontend: http://localhost:5173 (Vite dev server)
- Backend: http://localhost:8000 (Uvicorn with --reload)

---

## 🏭 Production Deployment

**Build and run optimized production images:**

```bash
# Clone the repository
git clone https://github.com/frankthetank001/POE2-PathOfCrafting.git
cd POE2-PathOfCrafting

# Build and start production deployment
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop
docker-compose -f docker-compose.prod.yml down
```

**Production features:**
- ✅ Optimized builds (smaller images)
- ✅ Frontend served by nginx on port 80
- ✅ Backend with 4 workers for better performance
- ✅ No source code mounting (immutable containers)
- ✅ Production-grade health checks

**Access:**
- Frontend: http://localhost (port 80)
- Backend: http://localhost:8000

---

## 📊 Pre-built Images

Images are automatically built and published to GitHub Container Registry on every push to `main`:

```
ghcr.io/frankthetank001/poe2-pathofcrafting-backend:latest
ghcr.io/frankthetank001/poe2-pathofcrafting-frontend:latest
```

**Pull images manually:**
```bash
docker pull ghcr.io/frankthetank001/poe2-pathofcrafting-backend:latest
docker pull ghcr.io/frankthetank001/poe2-pathofcrafting-frontend:latest
```

---

## 🗄️ Database Persistence

The SQLite database is stored in a Docker volume named `backend-data`.

**View volumes:**
```bash
docker volume ls | grep backend-data
```

**Backup database:**
```bash
# Copy database from volume to host
docker cp poe2-pathofcrafting-backend:/app/data/crafting.db ./crafting.db.backup
```

**Restore database:**
```bash
# Copy database from host to volume
docker cp ./crafting.db.backup poe2-pathofcrafting-backend:/app/data/crafting.db
docker-compose restart backend
```

**Fresh start (delete all data):**
```bash
docker-compose down -v  # -v removes volumes
```

---

## 🔧 Configuration

### Environment Variables

**Backend:**
- `ENVIRONMENT`: `development` or `production`
- `PYTHONUNBUFFERED`: `1` for real-time logs

**Frontend:**
- `VITE_API_URL`: Backend API URL (e.g., `http://localhost:8000`)

### Port Mapping

You can customize ports by editing the compose file:

```yaml
services:
  backend:
    ports:
      - "3000:8000"  # Map host:3000 -> container:8000
  frontend:
    ports:
      - "8080:5173"  # Map host:8080 -> container:5173
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Check database initialization
docker exec -it poe2-pathofcrafting-backend ls -la /app/data

# Restart with fresh database
docker-compose down -v
docker-compose up
```

### Frontend can't reach backend
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend environment
docker exec -it poe2-pathofcrafting-frontend env | grep VITE_API_URL

# Ensure backend is running
docker-compose ps
```

### Permission issues (Linux)
```bash
# Fix ownership of data directory
sudo chown -R $USER:$USER .
```

### Port already in use
```bash
# Find what's using the port
lsof -i :8000  # or :5173

# Change port in docker-compose.yml
# ports:
#   - "8001:8000"  # Use different host port
```

---

## 📝 Advanced Usage

### Run specific services
```bash
docker-compose up backend  # Only backend
docker-compose up frontend  # Only frontend
```

### Rebuild images
```bash
docker-compose build  # Rebuild all
docker-compose build backend  # Rebuild backend only
docker-compose up --build  # Rebuild and start
```

### Shell into containers
```bash
docker exec -it poe2-pathofcrafting-backend bash
docker exec -it poe2-pathofcrafting-frontend sh
```

### View resource usage
```bash
docker stats poe2-pathofcrafting-backend poe2-pathofcrafting-frontend
```

---

## 🆘 Support

- **Issues**: https://github.com/frankthetank001/POE2-PathOfCrafting/issues
- **Discussions**: https://github.com/frankthetank001/POE2-PathOfCrafting/discussions
- **Documentation**: https://github.com/frankthetank001/POE2-PathOfCrafting/blob/main/README.md
