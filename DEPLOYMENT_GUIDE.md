# 🚀 PRP AI Assistant Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the PRP AI Assistant system to production with full security, monitoring, and scalability features.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **CPU**: 2+ cores (4+ recommended)
- **Storage**: 20GB+ available space
- **Network**: HTTPS/SSL certificate for production domain

### Software Dependencies
- Docker 20.10+
- Docker Compose 2.0+
- Git
- OpenSSL (for generating secrets)

## 🔐 Security Setup

### 1. Generate Secrets
```bash
# Generate secure secrets
export SECRET_KEY=$(openssl rand -hex 32)
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -hex 16)
export GRAFANA_PASSWORD=$(openssl rand -hex 16)

# Save to production .env file
cat > .env.production << EOF
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
CLAUDE_API_KEY=your_claude_api_key_here
EOF
```

### 2. SSL Certificate Setup
```bash
# For Let's Encrypt (recommended)
sudo certbot certonly --webroot -w /var/www/html -d yourdomain.com

# Or use your existing certificates
mkdir -p ssl/
cp /path/to/your/certificate.crt ssl/
cp /path/to/your/private.key ssl/
```

## 🐳 Docker Deployment

### 1. Clone Repository
```bash
git clone https://github.com/your-org/prp-ai-assistant.git
cd prp-ai-assistant
```

### 2. Production Configuration
```bash
# Copy production environment
cp .env.production .env

# Copy production docker-compose
cp docker-compose.production.yml docker-compose.yml

# Create necessary directories
mkdir -p logs monitoring/data
```

### 3. Build and Deploy
```bash
# Build optimized production image
docker build -f Dockerfile.optimized -t prp-ai-assistant:latest .

# Deploy with docker-compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f prp-api
```

### 4. Initialize Database
```bash
# Run database migrations
docker-compose exec prp-api alembic upgrade head

# Create admin user
docker-compose exec prp-api python -c "
from auth import User
from prp_models import get_db_session
session = get_db_session()
admin = User(username='admin', email='admin@yourdomain.com', role='admin')
admin.set_password('secure_admin_password')
session.add(admin)
session.commit()
print('Admin user created')
"
```

## ☸️ Kubernetes Deployment (Alternative)

### 1. Create Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: prp-production
```

### 2. Secrets Configuration
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: prp-secrets
  namespace: prp-production
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key-here"
  JWT_SECRET_KEY: "your-jwt-secret-here"
  DATABASE_URL: "postgresql://user:pass@postgres:5432/prp"
  REDIS_URL: "redis://redis:6379/0"
  CLAUDE_API_KEY: "your-claude-api-key"
```

### 3. Application Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prp-api
  namespace: prp-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: prp-api
  template:
    metadata:
      labels:
        app: prp-api
    spec:
      containers:
      - name: prp-api
        image: prp-ai-assistant:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: prp-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 4. Deploy to Kubernetes
```bash
kubectl apply -f k8s/
kubectl get pods -n prp-production
kubectl logs -f deployment/prp-api -n prp-production
```

## 📊 Monitoring Setup

### 1. Access Monitoring Dashboards
- **Grafana**: http://your-domain:3000 (admin/your-grafana-password)
- **Prometheus**: http://your-domain:9090
- **Application Metrics**: http://your-domain:8000/metrics

### 2. Import Grafana Dashboards
```bash
# Import pre-configured dashboards
curl -X POST \
  http://admin:${GRAFANA_PASSWORD}@your-domain:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana-dashboard.json
```

### 3. Set Up Alerts
```yaml
# prometheus/alert_rules.yml
groups:
- name: prp_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(prp_http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(prp_http_request_duration_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
```

## 🔍 Health Checks & Validation

### 1. Application Health
```bash
# Check application health
curl -f http://your-domain/health

# Check compliance score
curl -s http://your-domain/api/admin/stats | jq '.compliance_score'

# Run security scan
docker run --rm -v $(pwd):/app bandit -r /app -f json
```

### 2. Performance Validation
```bash
# Load testing with k6
k6 run --vus 10 --duration 30s tests/performance/load-test.js

# Check database performance
docker-compose exec postgres psql -U prp_user -d prp_production -c "
SELECT schemaname,tablename,attname,n_distinct,correlation 
FROM pg_stats 
WHERE schemaname = 'public';"
```

### 3. Security Validation
```bash
# SSL/TLS check
curl -I https://your-domain

# Security headers check
curl -I https://your-domain | grep -E "(X-Frame-Options|X-Content-Type-Options|Strict-Transport-Security)"

# Authentication check
curl -X POST https://your-domain/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"invalid"}' \
  | jq '.error'
```

## 🔄 Backup & Recovery

### 1. Database Backup
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T postgres pg_dump -U prp_user prp_production | gzip > backups/prp_backup_${TIMESTAMP}.sql.gz
aws s3 cp backups/prp_backup_${TIMESTAMP}.sql.gz s3://your-backup-bucket/
EOF

chmod +x backup.sh

# Schedule with cron
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### 2. Recovery Process
```bash
# Restore from backup
gunzip -c backups/prp_backup_TIMESTAMP.sql.gz | \
docker-compose exec -T postgres psql -U prp_user prp_production
```

## 📈 Scaling

### 1. Horizontal Scaling
```bash
# Scale API instances
docker-compose up -d --scale prp-api=3

# Scale worker instances
docker-compose up -d --scale prp-worker=4
```

### 2. Database Optimization
```sql
-- Create indexes for performance
CREATE INDEX CONCURRENTLY idx_prp_created_at ON prp_records(created_at);
CREATE INDEX CONCURRENTLY idx_analytics_prp_id ON prp_analytics(prp_id);
CREATE INDEX CONCURRENTLY idx_users_username ON users(username);

-- Update table statistics
ANALYZE;
```

### 3. Cache Optimization
```bash
# Increase Redis memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb

# Monitor cache hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace_hits
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check logs
docker-compose logs prp-api

# Check environment variables
docker-compose exec prp-api env | grep -E "(SECRET_KEY|DATABASE_URL)"

# Validate configuration
docker-compose exec prp-api python -c "from config import config; config.validate()"
```

#### 2. Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready

# Test connection
docker-compose exec prp-api python -c "
from sqlalchemy import create_engine
from config import config
engine = create_engine(config.DATABASE_URL)
with engine.connect() as conn:
    print('Database connection successful')
"
```

#### 3. High Memory Usage
```bash
# Check memory usage
docker stats

# Optimize database connections
docker-compose exec prp-api python -c "
from config import config
print(f'Pool size: {config.SQLALCHEMY_ENGINE_OPTIONS[\"pool_size\"]}')
print(f'Max overflow: {config.SQLALCHEMY_ENGINE_OPTIONS[\"max_overflow\"]}')
"
```

#### 4. Cache Issues
```bash
# Check Redis memory
docker-compose exec redis redis-cli INFO memory

# Clear cache if needed
curl -X POST https://your-domain/api/admin/cache/clear \
  -H "Authorization: Bearer your-admin-token"
```

## 📚 Maintenance

### Daily Tasks
- [ ] Check application health dashboard
- [ ] Review error logs
- [ ] Monitor response times
- [ ] Check disk space usage

### Weekly Tasks  
- [ ] Review security scan results
- [ ] Update dependency vulnerabilities
- [ ] Analyze performance metrics
- [ ] Test backup restoration

### Monthly Tasks
- [ ] Update system packages
- [ ] Review and rotate secrets
- [ ] Performance optimization
- [ ] Capacity planning review

## 📞 Support

### Emergency Contacts
- **DevOps Team**: devops@company.com
- **Security Team**: security@company.com
- **Incident Response**: +1-xxx-xxx-xxxx

### Monitoring Alerts
- **Slack Channel**: #prp-alerts
- **PagerDuty**: prp-production-incidents
- **Email**: alerts@company.com

### Documentation
- **API Docs**: https://your-domain/docs
- **Monitoring**: https://grafana.your-domain.com
- **Logs**: https://logs.your-domain.com

---

## ✅ Deployment Checklist

Before going live, ensure:

- [ ] All secrets are properly configured
- [ ] SSL certificates are valid and auto-renewing
- [ ] Database migrations are up to date
- [ ] All health checks are passing
- [ ] Monitoring and alerting are configured
- [ ] Backup and recovery procedures are tested
- [ ] Load testing has been performed
- [ ] Security scanning shows no critical issues
- [ ] Compliance score is above 85%
- [ ] Documentation is up to date
- [ ] Team is trained on operational procedures

**🎉 Your PRP AI Assistant is now ready for production!**