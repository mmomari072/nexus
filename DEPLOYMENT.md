# AgileAI Deployment Guide

## Overview

The AgileAI backlog feature is production-ready and can be deployed to staging in multiple ways:

1. **Docker** (Recommended) - Easy containerized deployment
2. **Systemd Service** (Linux) - Native systemd integration
3. **Manual** - Direct Python installation

---

## Option 1: Docker Deployment (Recommended)

### Prerequisites
- Docker Engine (20.10+)
- Docker Compose (1.29+)

### Quick Start

```bash
# Navigate to project root
cd H:\MyCodes\MyGitHub\nexus

# Build and start containers
docker-compose up -d

# Check logs
docker-compose logs -f agileai-api

# Stop services
docker-compose down
```

### Access the API
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### Database
- Location: `./data/agileai.db`
- Persists across container restarts
- Auto-initialized on first run

### Configuration

Environment variables in `docker-compose.yml`:
```yaml
environment:
  AGILEAI_DB_PATH: /app/data/agileai.db    # Database location
  PYTHONUNBUFFERED: "1"                    # Real-time logging
```

---

## Option 2: Systemd Service (Linux)

### Create Service File

Create `/etc/systemd/system/agileai.service`:

```ini
[Unit]
Description=AgileAI FastAPI Application
After=network.target
Wants=network-online.target

[Service]
Type=notify
User=agileai
WorkingDirectory=/opt/agileai
Environment="PATH=/opt/agileai/venv/bin"
Environment="AGILEAI_DB_PATH=/var/lib/agileai/agileai.db"
ExecStart=/opt/agileai/venv/bin/python -m uvicorn agileai.api.main:app --host 0.0.0.0 --port 8000 --workers 4

Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal
SyslogIdentifier=agileai

[Install]
WantedBy=multi-user.target
```

### Setup

```bash
# Create application directory
sudo mkdir -p /opt/agileai
sudo mkdir -p /var/lib/agileai
sudo chown -R agileai:agileai /opt/agileai /var/lib/agileai

# Copy application files
sudo cp -r . /opt/agileai/

# Create virtual environment
cd /opt/agileai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable agileai
sudo systemctl start agileai

# Check status
sudo systemctl status agileai
sudo journalctl -u agileai -f
```

---

## Option 3: Manual Deployment (Linux/macOS)

### Setup

```bash
# Clone repository
git clone <repo-url> /opt/agileai
cd /opt/agileai

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
export AGILEAI_DB_PATH=/var/lib/agileai/agileai.db
mkdir -p /var/lib/agileai

# Run tests to verify
pytest tests/test_backlog.py -v

# Start server
uvicorn agileai.api.main:app --host 0.0.0.0 --port 8000
```

---

## Production Deployment Checklist

- [ ] Clone repository to staging server
- [ ] Install dependencies from `requirements.txt`
- [ ] Set environment variables (see Configuration section)
- [ ] Initialize database (auto-runs on first startup)
- [ ] Run full test suite to verify: `pytest tests/test_backlog.py -v`
- [ ] Configure reverse proxy (nginx/Apache)
- [ ] Set up SSL/TLS certificates
- [ ] Configure logging and monitoring
- [ ] Set up backup strategy for SQLite database
- [ ] Test health check endpoint: `curl http://localhost:8000/health`
- [ ] Load test with sample data
- [ ] Document any custom configurations

---

## Reverse Proxy Setup (nginx)

### Configuration

```nginx
upstream agileai {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.agileai.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.agileai.example.com;

    ssl_certificate /etc/letsencrypt/live/api.agileai.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.agileai.example.com/privkey.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass http://agileai;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    location /health {
        proxy_pass http://agileai;
        access_log off;
    }
}
```

---

## Monitoring and Logging

### Systemd Logging
```bash
# Follow logs
sudo journalctl -u agileai -f

# Last 100 lines
sudo journalctl -u agileai -n 100

# By priority
sudo journalctl -u agileai -p err
```

### Docker Logging
```bash
# Follow logs
docker-compose logs -f agileai-api

# Last 100 lines
docker-compose logs --tail=100 agileai-api
```

### Log Levels
Set via environment variable:
```bash
# For FastAPI debug logging:
UVICORN_LOG_LEVEL=debug
```

---

## Backup Strategy

### SQLite Database Backup

```bash
# Manual backup
cp /var/lib/agileai/agileai.db /backups/agileai-$(date +%Y%m%d).db

# Automated backup (cron)
0 2 * * * cp /var/lib/agileai/agileai.db /backups/agileai-$(date +\%Y\%m\%d).db
```

### Docker Volume Backup
```bash
# Backup database from Docker volume
docker run --rm \
  -v agileai_data:/data \
  -v /backups:/backups \
  alpine tar czf /backups/agileai-db-$(date +%Y%m%d).tar.gz -C /data agileai.db
```

---

## Troubleshooting

### Application won't start
```bash
# Check if port is in use
lsof -i :8000

# Check logs
sudo journalctl -u agileai -n 50

# Verify dependencies
pip install -r requirements.txt
```

### Database errors
```bash
# Verify database exists
ls -la /var/lib/agileai/agileai.db

# Check permissions
chmod 644 /var/lib/agileai/agileai.db
chown agileai:agileai /var/lib/agileai/agileai.db
```

### API not responding
```bash
# Test health endpoint
curl -v http://localhost:8000/health

# Check reverse proxy configuration
nginx -t  # for nginx
```

---

## Performance Tuning

### FastAPI Workers
```bash
# Multiple workers (production)
uvicorn agileai.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

### Database Connection Pool
Configured automatically based on CPU count. For SQLite, typically optimal at current settings.

### Caching
Implement HTTP caching headers in nginx for frequently accessed endpoints.

---

## Support

For issues or questions:
1. Check logs (see Monitoring section)
2. Review DEVELOPMENT_REPORT.md for architecture
3. Check API.md for endpoint reference
4. Run test suite: `pytest tests/test_backlog.py -v`

---

**Status**: Ready for staging deployment ✓
