# ShadowLedger Production Deployment Guide

## 🚀 Overview

This guide covers deploying ShadowLedger blockchain to production with enterprise-grade security, monitoring, and scalability.

## 📋 Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose
- 4GB+ RAM, 2+ CPU cores
- 50GB+ storage
- Public IP address (for P2P networking)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Server    │    │   P2P Network   │
│   (Nginx)       │◄──►│   (FastAPI)     │◄──►│   (Port 8888)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SSL/TLS       │    │   Blockchain    │    │   Monitoring    │
│   Termination   │    │   Storage       │    │   (Logs/Metrics)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd tx-shadownet
chmod +x start.sh
```

### 2. Environment Configuration

Create `.env` file:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# P2P Configuration
P2P_PORT=8888
BOOTSTRAP_NODES=node1.example.com,node2.example.com

# Security
RATE_LIMIT_PER_MINUTE=60
MAX_TRANSACTION_AMOUNT=1000000

# Database/Storage
DATA_DIR=/app/data
LOG_DIR=/app/logs

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### 3. Docker Deployment

```bash
# Build and start services
docker-compose up -d

# Start with mining (optional)
docker-compose --profile mining up -d

# Check status
docker-compose ps
docker-compose logs -f
```

### 4. Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Start P2P node
python p2p.py --port 8888 &

# Start API server with gunicorn
gunicorn api:app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 100
```

## 🔐 Security Configuration

### 1. Firewall Setup

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # API
sudo ufw allow 8888/tcp  # P2P
sudo ufw enable
```

### 2. SSL/TLS with Nginx

Create `/etc/nginx/sites-available/shadowledger`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Rate Limiting

Configure in `api.py`:

```python
# Adjust rate limits based on your needs
rate_limiter = RateLimiter(requests_per_minute=30)  # More restrictive
```

## 📊 Monitoring & Logging

### 1. Log Management

```bash
# Create log rotation
sudo tee /etc/logrotate.d/shadowledger << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 shadowledger shadowledger
    postrotate
        systemctl reload shadowledger
    endscript
}
EOF
```

### 2. Health Monitoring

```bash
# Create systemd service
sudo tee /etc/systemd/system/shadowledger.service << EOF
[Unit]
Description=ShadowLedger Blockchain Node
After=network.target

[Service]
Type=simple
User=shadowledger
WorkingDirectory=/app
ExecStart=/app/start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable shadowledger
sudo systemctl start shadowledger
```

### 3. Metrics Collection

Add Prometheus metrics endpoint:

```python
# Add to api.py
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🔄 Scaling & High Availability

### 1. Load Balancing

```nginx
upstream shadowledger_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://shadowledger_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Database Scaling

For high-volume deployments, consider:

- PostgreSQL for transaction storage
- Redis for mempool caching
- Distributed file storage (S3, Ceph)

### 3. P2P Network Scaling

```python
# Configure multiple bootstrap nodes
BOOTSTRAP_NODES = [
    "node1.shadowledger.com",
    "node2.shadowledger.com", 
    "node3.shadowledger.com"
]
```

## 🛠️ Operations

### 1. Backup Strategy

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/shadowledger"

mkdir -p $BACKUP_DIR

# Backup blockchain
cp blockchain.json $BACKUP_DIR/blockchain_$DATE.json

# Backup mempool
cp mempool.json $BACKUP_DIR/mempool_$DATE.json

# Compress
tar -czf $BACKUP_DIR/shadowledger_$DATE.tar.gz $BACKUP_DIR/*_$DATE.json

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 2. Update Procedure

```bash
# 1. Stop services
docker-compose down

# 2. Backup current state
./backup.sh

# 3. Pull latest code
git pull origin main

# 4. Rebuild and restart
docker-compose build
docker-compose up -d

# 5. Verify health
curl http://localhost:8000/health
```

### 3. Disaster Recovery

```bash
# Restore from backup
tar -xzf shadowledger_20231201_120000.tar.gz
cp blockchain_20231201_120000.json blockchain.json
cp mempool_20231201_120000.json mempool.json

# Restart services
docker-compose restart
```

## 📈 Performance Tuning

### 1. System Optimization

```bash
# Increase file descriptors
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize kernel parameters
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

### 2. Application Tuning

```python
# Optimize gunicorn workers
# Workers = (2 x CPU cores) + 1
gunicorn api:app \
    --workers 8 \
    --worker-connections 1000 \
    --max-requests 2000 \
    --max-requests-jitter 200
```

## 🔍 Troubleshooting

### Common Issues

1. **P2P Connection Issues**
   ```bash
   # Check firewall
   sudo ufw status
   
   # Test connectivity
   telnet peer-ip 8888
   ```

2. **High Memory Usage**
   ```bash
   # Monitor memory
   htop
   
   # Check for memory leaks
   docker stats
   ```

3. **Slow API Response**
   ```bash
   # Check logs
   tail -f logs/api.log
   
   # Monitor database
   du -sh data/
   ```

### Debug Commands

```bash
# Check service status
docker-compose ps
systemctl status shadowledger

# View logs
docker-compose logs -f api
tail -f logs/api.log

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/status

# Check P2P connections
curl http://localhost:8000/network/peers
```

## 📚 API Documentation

### Key Endpoints

- `GET /health` - Health check
- `GET /status` - System status
- `POST /wallet/create` - Create wallet
- `GET /wallet/{address}/balance` - Get balance
- `POST /transaction/send` - Send transaction
- `GET /blockchain` - Get blockchain
- `GET /network/peers` - Get peers

### CLI Usage

```bash
# Create wallet
python cli.py wallet create

# Send transaction
python cli.py tx send --from addr1 --to addr2 --amount 10 --key privkey

# Get blockchain info
python cli.py blockchain info
```

## 🎯 Production Checklist

- [ ] SSL/TLS configured
- [ ] Firewall rules set
- [ ] Rate limiting enabled
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Health checks working
- [ ] Load balancing configured
- [ ] Security headers set
- [ ] Error handling tested
- [ ] Performance optimized
- [ ] Documentation updated

## 🆘 Support

For production support:

1. Check logs: `tail -f logs/*.log`
2. Monitor metrics: `curl http://localhost:8000/metrics`
3. Test connectivity: `python cli.py network peers`
4. Verify blockchain: `python cli.py blockchain info`

## 📄 License

This deployment guide is part of the ShadowLedger project. Ensure compliance with all applicable licenses and regulations. 