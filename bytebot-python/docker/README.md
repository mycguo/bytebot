# Bytebot Python - Docker Deployment

Complete Docker deployment configuration for the Bytebot Python AI Desktop Agent.

## Quick Start

### 1. Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- At least one AI API key (Anthropic, OpenAI, or Google)

### 2. Configuration
```bash
# Copy environment template
cp docker/.env.example docker/.env

# Edit with your API keys
nano docker/.env
```

**Required:** Add at least one AI API key:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OR
OPENAI_API_KEY=sk-your-key-here
# OR  
GEMINI_API_KEY=your-key-here
```

### 3. Deploy
```bash
# Production deployment
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Check status
docker-compose -f docker/docker-compose.yml ps
```

### 4. Access
- **Web UI**: http://localhost:9992
- **AI Agent API**: http://localhost:9996
- **Computer Control API**: http://localhost:9995
- **Database**: localhost:5432

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │    │   AI Agent      │    │Computer Control │
│   (Streamlit)   │    │   (FastAPI)     │    │   (FastAPI)     │
│   Port: 9992    │    │   Port: 9996    │    │   Port: 9995    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   Port: 5432    │
                    └─────────────────┘
```

## Services

### PostgreSQL Database
- **Image**: postgres:16-alpine
- **Port**: 5432
- **Data**: Persisted in `postgres_data` volume
- **Health checks**: Built-in readiness checks

### Computer Control Service
- **Build**: Custom Python 3.11 image
- **Port**: 9995
- **Features**: Virtual display (Xvfb), desktop automation
- **Privileges**: Requires `privileged: true` for system access
- **Health check**: HTTP endpoint `/health`

### AI Agent Service
- **Build**: Custom Python 3.11 image
- **Port**: 9996
- **Features**: Task processing, AI integration, database ORM
- **Dependencies**: Database, Computer Control
- **Health check**: HTTP endpoint `/health`

### Web UI Service
- **Build**: Custom Python 3.11 image
- **Port**: 9992
- **Features**: Streamlit interface, task management, desktop viewer
- **Dependencies**: AI Agent, Computer Control
- **Health check**: Streamlit health endpoint

## Development

### Development Mode
```bash
# Start development environment
docker-compose -f docker/docker-compose.dev.yml up -d

# With hot reload and debug logging
# Volumes mounted for live code changes
```

### Building Images
```bash
# Build all images
docker-compose -f docker/docker-compose.yml build

# Build specific service
docker-compose -f docker/docker-compose.yml build ai-agent

# No cache rebuild
docker-compose -f docker/docker-compose.yml build --no-cache
```

### Debugging
```bash
# View logs for specific service
docker-compose -f docker/docker-compose.yml logs -f ai-agent

# Execute commands in running container
docker-compose -f docker/docker-compose.yml exec ai-agent bash

# Check service health
docker-compose -f docker/docker-compose.yml ps
```

## Environment Variables

### Required
- `ANTHROPIC_API_KEY` - Anthropic Claude API key
- `OPENAI_API_KEY` - OpenAI API key  
- `GEMINI_API_KEY` - Google Gemini API key

*At least one AI API key is required*

### Optional
- `POSTGRES_PASSWORD` - Database password (default: postgres)
- `POSTGRES_USER` - Database user (default: postgres)
- `POSTGRES_DB` - Database name (default: bytebotdb)
- `LOG_LEVEL` - Logging level (default: INFO)

### Service URLs (Internal)
- `DATABASE_URL` - Full PostgreSQL connection string
- `COMPUTER_CONTROL_URL` - Internal computer control service URL

## Volumes

### Persistent Data
- `postgres_data` - PostgreSQL data directory
- Survives container restarts and updates

### Development Volumes
- Source code mounted for live editing
- Changes reflect immediately without rebuild

## Networking

### Internal Network
- `bytebot-network` - Bridge network for service communication
- Services communicate using container names as hostnames
- Isolated from other Docker networks

### External Ports
- `9992` - Web UI (HTTP)
- `9995` - Computer Control API (HTTP)  
- `9996` - AI Agent API (HTTP)
- `5432` - PostgreSQL (TCP)

## Security Considerations

### Production Deployment
1. **Change default passwords**
   ```env
   POSTGRES_PASSWORD=your-secure-password-here
   ```

2. **Restrict external access**
   - Only expose necessary ports
   - Use reverse proxy (nginx, Traefik)
   - Enable HTTPS/TLS

3. **API Key Security**
   - Store keys in Docker secrets or external secret management
   - Never commit keys to version control
   - Rotate keys regularly

4. **Network Security**  
   - Use custom bridge networks
   - Implement network policies
   - Monitor container communication

### Development vs Production
- Development: All ports exposed, debug logging
- Production: Minimal exposure, secure defaults, health monitoring

## Monitoring

### Health Checks
All services include Docker health checks:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9995/health"]
  interval: 30s
  timeout: 3s
  retries: 3
```

### Logging
```bash
# View all logs
docker-compose logs -f

# Service-specific logs  
docker-compose logs -f ai-agent

# Follow new logs only
docker-compose logs -f --tail=0
```

### Resource Usage
```bash
# Container stats
docker stats

# Resource usage by service
docker-compose top
```

## Troubleshooting

### Common Issues

**Services not starting**
```bash
# Check logs
docker-compose logs

# Verify environment variables
docker-compose config

# Check port conflicts
netstat -tlnp | grep :9992
```

**Database connection issues**
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U postgres -d bytebotdb -c '\dt'
```

**API key errors**
```bash
# Verify environment variables are loaded
docker-compose exec ai-agent env | grep API_KEY

# Check service logs for authentication errors
docker-compose logs ai-agent | grep -i error
```

**Desktop automation not working**
```bash
# Check virtual display
docker-compose exec computer-control echo $DISPLAY

# Verify privileged mode
docker inspect bytebot-python-computer-control | grep Privileged

# Check X11 dependencies
docker-compose exec computer-control xdpyinfo -display :99
```

### Recovery

**Reset everything**
```bash
# Stop and remove all containers/volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Fresh start
docker-compose up -d
```

**Database reset**
```bash
# Remove only database volume
docker-compose down
docker volume rm bytebot-python_postgres_data
docker-compose up -d
```

## Updates

### Service Updates
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Zero-downtime rolling update
docker-compose up -d --force-recreate --no-deps ai-agent
```

### Backup
```bash
# Database backup
docker-compose exec postgres pg_dump -U postgres bytebotdb > backup.sql

# Volume backup
docker run --rm -v bytebot-python_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

## Performance

### Resource Requirements
- **Minimum**: 2GB RAM, 2 CPU cores, 10GB disk
- **Recommended**: 4GB RAM, 4 CPU cores, 20GB disk
- **Database**: Additional 1GB RAM for PostgreSQL

### Scaling
```bash
# Scale web UI instances (behind load balancer)
docker-compose up -d --scale web-ui=3

# Resource limits
docker-compose --compatibility up -d
```

## Integration

### External Services
- **Reverse Proxy**: nginx, Traefik, Apache
- **Load Balancer**: HAProxy, AWS ALB, GCP Load Balancer  
- **Monitoring**: Prometheus, Grafana, ELK Stack
- **Secret Management**: Vault, AWS Secrets Manager, Azure Key Vault