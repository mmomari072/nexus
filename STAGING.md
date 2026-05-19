# Staging Deployment - Quick Start

## One-Command Deployment

```bash
cd /path/to/nexus
docker-compose up -d
```

Done! API is running at http://localhost:8000

---

## Verify Deployment

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "agileai-api"
}
```

### Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## Run Tests Against Staging

```bash
# From project root
.venv_main/Scripts/pytest tests/test_backlog.py -v

# Or from container
docker-compose exec agileai-api pytest tests/test_backlog.py -v
```

Expected: **15/15 tests passing**

---

## Try the API

### List backlog
```bash
curl -X GET "http://localhost:8000/api/v1/backlog/projects/proj-1"
```

### Get Swagger UI and try interactively
Open http://localhost:8000/docs in browser

### Estimate issue
```bash
curl -X POST "http://localhost:8000/api/v1/backlog/projects/proj-1/estimate" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id": "issue-1",
    "difficulty": "medium",
    "importance": "high",
    "child_count": 0,
    "has_external_dependencies": false,
    "issue_type": "task"
  }'
```

---

## Monitor Staging

### Follow logs
```bash
docker-compose logs -f agileai-api
```

### Check container status
```bash
docker-compose ps
```

### Stop staging
```bash
docker-compose down
```

### Stop and remove data
```bash
docker-compose down -v
```

---

## Database

- **Location**: `./data/agileai.db`
- **Auto-initialized**: Yes, on first startup
- **Persistent**: Survives container restarts
- **Accessible from**: Inside container at `/app/data/agileai.db`

---

## Scale to Multiple Workers

Edit `docker-compose.yml` and change the CMD:

```yaml
CMD ["uvicorn", "agileai.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Then restart:
```bash
docker-compose restart agileai-api
```

---

## Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class BacklogUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health(self):
        self.client.get("/health")
    
    @task(3)
    def list_backlog(self):
        self.client.get("/api/v1/backlog/projects/proj-1")
    
    @task(2)
    def estimate(self):
        self.client.post("/api/v1/backlog/projects/proj-1/estimate", json={
            "issue_id": "issue-1",
            "difficulty": "medium",
            "importance": "high",
            "child_count": 0,
            "has_external_dependencies": False,
            "issue_type": "task"
        })
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10
```

Then visit http://localhost:8089 to control the load test.

---

## Troubleshooting

### Port already in use
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it or use different port
docker-compose down
```

### Database locked
```bash
# Restart container
docker-compose restart agileai-api
```

### Out of memory
```bash
# Check limits in docker-compose.yml
# Increase or remove memory restrictions
```

### Logs show errors
```bash
# View full logs
docker-compose logs agileai-api | tail -50

# Check if tests pass
docker-compose exec agileai-api pytest tests/test_backlog.py::test_estimate_issue_trivial -v
```

---

## Next Steps After Staging

1. ✓ Verify API is responding
2. ✓ Run full test suite  
3. ✓ Load test with realistic data
4. ✓ Set up monitoring/alerting
5. ✓ Configure SSL/TLS
6. ✓ Deploy to production

---

**Status**: Staging deployment ready to go ✓
