# Deployment Guide

This guide covers deploying Profit Tracker AI to various platforms.

## Table of Contents
1. [Heroku Deployment](#heroku-deployment)
2. [DigitalOcean Deployment](#digitalocean-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Manual VPS Deployment](#manual-vps-deployment)
5. [Environment Variables](#environment-variables)
6. [SSL Configuration](#ssl-configuration)
7. [Database Setup](#database-setup)
8. [Monitoring](#monitoring)

## Heroku Deployment

### One-Click Deploy
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/WeberG619/profit-tracker-ai)

### Manual Heroku Setup

1. Install Heroku CLI:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

2. Login to Heroku:
```bash
heroku login
```

3. Create a new app:
```bash
heroku create your-app-name
```

4. Add PostgreSQL addon:
```bash
heroku addons:create heroku-postgresql:mini
```

5. Add Redis addon:
```bash
heroku addons:create heroku-redis:mini
```

6. Set environment variables:
```bash
heroku config:set ANTHROPIC_API_KEY=your_api_key
heroku config:set TWILIO_ACCOUNT_SID=your_account_sid
heroku config:set TWILIO_AUTH_TOKEN=your_auth_token
heroku config:set TWILIO_PHONE_NUMBER=your_phone_number
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
```

7. Deploy:
```bash
git push heroku main
```

8. Run migrations:
```bash
heroku run python -m flask db upgrade
```

9. Scale workers:
```bash
heroku ps:scale web=1 worker=1
```

## DigitalOcean Deployment

### Using App Platform

1. Fork the repository to your GitHub account

2. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)

3. Click "Create App" and connect your GitHub repository

4. Configure app settings:
   - **Web Service**: 
     - Build Command: `pip install -r requirements.txt`
     - Run Command: `gunicorn wsgi:app`
   - **Worker Service**:
     - Run Command: `python -m scheduler`

5. Add environment variables in the App settings

6. Add managed PostgreSQL database

7. Deploy the app

### Using Droplet

1. Create a Ubuntu 22.04 droplet

2. SSH into the droplet:
```bash
ssh root@your_droplet_ip
```

3. Install dependencies:
```bash
apt update && apt upgrade -y
apt install python3-pip python3-venv nginx postgresql postgresql-contrib redis-server -y
```

4. Clone the repository:
```bash
git clone https://github.com/WeberG619/profit-tracker-ai.git
cd profit-tracker-ai
```

5. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

6. Set up PostgreSQL:
```bash
sudo -u postgres psql
CREATE DATABASE profit_tracker;
CREATE USER profit_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE profit_tracker TO profit_user;
\q
```

7. Configure environment:
```bash
cp .env.example .env
nano .env  # Edit with your values
```

8. Set up systemd services:
```bash
# Web service
cat > /etc/systemd/system/profit-tracker.service << EOF
[Unit]
Description=Profit Tracker Web Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/root/profit-tracker-ai
Environment="PATH=/root/profit-tracker-ai/venv/bin"
ExecStart=/root/profit-tracker-ai/venv/bin/gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 4

[Install]
WantedBy=multi-user.target
EOF

# Worker service
cat > /etc/systemd/system/profit-tracker-worker.service << EOF
[Unit]
Description=Profit Tracker Worker Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/root/profit-tracker-ai
Environment="PATH=/root/profit-tracker-ai/venv/bin"
ExecStart=/root/profit-tracker-ai/venv/bin/python -m scheduler

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable profit-tracker profit-tracker-worker
systemctl start profit-tracker profit-tracker-worker
```

9. Configure Nginx:
```bash
cat > /etc/nginx/sites-available/profit-tracker << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /static {
        alias /root/profit-tracker-ai/app/static;
    }

    client_max_body_size 20M;
}
EOF

ln -s /etc/nginx/sites-available/profit-tracker /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx
```

## Docker Deployment

### Using Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/WeberG619/profit-tracker-ai.git
cd profit-tracker-ai
```

2. Create .env file:
```bash
cp .env.example .env
# Edit .env with your values
```

3. Build and run:
```bash
docker-compose up -d
```

4. Run migrations:
```bash
docker-compose exec web flask db upgrade
```

### Using Docker Swarm

1. Initialize swarm:
```bash
docker swarm init
```

2. Create secrets:
```bash
echo "your_api_key" | docker secret create anthropic_api_key -
echo "your_account_sid" | docker secret create twilio_account_sid -
echo "your_auth_token" | docker secret create twilio_auth_token -
```

3. Deploy stack:
```bash
docker stack deploy -c docker-compose.yml profit-tracker
```

## Environment Variables

Required environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | `sk-ant-...` |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | `...` |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number | `+1234567890` |
| `SECRET_KEY` | Flask secret key | `your-secret-key` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `REDIS_URL` | Redis connection string | `redis://...` |

Optional environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_CONTENT_LENGTH` | Max upload size | `16777216` (16MB) |
| `RATE_LIMIT` | API rate limit | `100 per minute` |

## SSL Configuration

### Using Let's Encrypt

1. Install Certbot:
```bash
apt install certbot python3-certbot-nginx -y
```

2. Obtain certificate:
```bash
certbot --nginx -d your-domain.com -d www.your-domain.com
```

3. Auto-renewal:
```bash
certbot renew --dry-run
```

### Using Cloudflare

1. Add your domain to Cloudflare
2. Update DNS records to point to your server
3. Enable "Full (strict)" SSL mode
4. Configure Nginx to accept Cloudflare IPs only

## Database Setup

### PostgreSQL Optimization

Edit `/etc/postgresql/15/main/postgresql.conf`:

```conf
# Memory
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Connections
max_connections = 100

# Write performance
checkpoint_segments = 32
checkpoint_completion_target = 0.9

# Query planning
random_page_cost = 1.1
```

### Backup Configuration

Create backup script:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATABASE="profit_tracker"

mkdir -p $BACKUP_DIR
pg_dump $DATABASE | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-postgres.sh
```

## Monitoring

### Health Checks

Add health check endpoint monitoring:
- Endpoint: `/health`
- Expected response: `200 OK`
- Check interval: 5 minutes

### Application Monitoring

1. **New Relic** (Heroku):
```bash
heroku addons:create newrelic:wayne
```

2. **Datadog**:
```bash
pip install datadog
```

Add to your app:
```python
from datadog import initialize, statsd

initialize(api_key='your_api_key')
statsd.increment('receipts.processed')
```

3. **Sentry** for error tracking:
```bash
pip install sentry-sdk[flask]
```

Initialize in app:
```python
import sentry_sdk
sentry_sdk.init(
    dsn="your_sentry_dsn",
    integrations=[FlaskIntegration()]
)
```

### Log Management

1. **Papertrail** (Heroku):
```bash
heroku addons:create papertrail:choklad
```

2. **ELK Stack** (self-hosted):
- Configure Filebeat to ship logs
- Use Logstash for processing
- View in Kibana

### Performance Monitoring

1. Monitor key metrics:
   - Response times
   - Database query times
   - Receipt processing times
   - SMS processing success rate

2. Set up alerts for:
   - High error rates (>1%)
   - Slow response times (>2s)
   - Failed SMS processing
   - Database connection issues

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Check DATABASE_URL format
   - Verify PostgreSQL is running
   - Check firewall rules

2. **SMS not receiving**:
   - Verify Twilio webhook URL
   - Check Twilio credentials
   - Ensure public URL is accessible

3. **Receipt processing failing**:
   - Verify Anthropic API key
   - Check file upload limits
   - Monitor API rate limits

4. **High memory usage**:
   - Reduce worker count
   - Implement image size limits
   - Use Redis for caching

### Debug Mode

Enable debug logging:
```bash
export FLASK_ENV=development
export LOG_LEVEL=DEBUG
```

Check logs:
```bash
# Heroku
heroku logs --tail

# Docker
docker-compose logs -f

# Systemd
journalctl -u profit-tracker -f
```