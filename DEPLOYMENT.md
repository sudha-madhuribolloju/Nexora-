# NEXORA – AI Classroom Platform: Deployment Guide

This guide provides comprehensive instructions for deploying **NEXORA – AI Classroom Platform** across production environments, including Oracle Cloud Infrastructure (OCI), Amazon Web Services (AWS), Microsoft Azure, and generic Linux Virtual Machines.

---

## 1. Prerequisites

- Docker v24.0+ and Docker Compose v2.20+ installed on target server.
- Registered Domain Name with DNS A records pointing to server IP.
- SSL Certificate (Let's Encrypt / Certbot or custom `.crt` / `.key` files).
- Google Gemini API Key (`GOOGLE_API_KEY`).

---

## 2. Generic Linux VM Deployment (Ubuntu 22.04 / 24.04 LTS)

### Step 1: Clone Repository & Configure Environment

```bash
git clone https://github.com/your-org/nexora-ai-classroom.git /opt/nexora
cd /opt/nexora

# Create Production Environment File
cat << 'EOF' > .env
POSTGRES_DB=nexora_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=prod_super_secure_db_password_2026
JWT_SECRET=prod_jwt_super_secret_signing_key_2026
GOOGLE_API_KEY=your_gemini_api_key_here
ENVIRONMENT=production
EOF
```

### Step 2: Configure SSL Certificates (Let's Encrypt / Certbot)

```bash
sudo apt update && sudo apt install -y certbot
sudo certbot certonly --standalone -d nexora.yourdomain.com

mkdir -p ./nginx/certs
sudo cp /etc/letsencrypt/live/nexora.yourdomain.com/fullchain.pem ./nginx/certs/
sudo cp /etc/letsencrypt/live/nexora.yourdomain.com/privkey.pem ./nginx/certs/
```

### Step 3: Launch Production Containers

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 3. OCI (Oracle Cloud Infrastructure) Deployment

1. **Provision Compute Instance**: Create an Ampere A1 (ARM64) or E4 (AMD64) Ubuntu instance in OCI Console.
2. **Configure Security List**: Add ingress rules for Port 80 (HTTP) and Port 443 (HTTPS) in the VCN Security List.
3. **Configure Host Firewall (`iptables`)**:
   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```
4. Follow **Section 2 (Generic Linux VM Deployment)** to launch.

---

## 4. AWS (Amazon Web Services EC2) Deployment

1. **Launch EC2 Instance**: Select Ubuntu 22.04 LTS (t3.medium or t4g.medium recommended).
2. **Configure Security Group**: Allow Inbound SSH (22), HTTP (80), HTTPS (443).
3. **Attach Elastic IP**: Associate EIP to ensure static IP across restarts.
4. Follow **Section 2 (Generic Linux VM Deployment)** to launch.

---

## 5. Azure (Virtual Machines) Deployment

1. **Create Virtual Machine**: Select Standard_B2s or Standard_D2s_v5 Ubuntu 22.04 LTS.
2. **Configure Networking**: Add Inbound Port Rules for 80 (HTTP) and 443 (HTTPS).
3. Follow **Section 2 (Generic Linux VM Deployment)** to launch.

---

## 6. Database Backup & Migration Strategy

### Automated PostgreSQL Backup Script (`/opt/nexora/scripts/backup.sh`)

```bash
#!/bin/bash
BACKUP_DIR="/opt/nexora/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p $BACKUP_DIR

docker exec nexora-postgres-prod pg_dump -U postgres nexora_db | gzip > "$BACKUP_DIR/nexora_backup_$TIMESTAMP.sql.gz"

# Retain last 14 days of backups
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +14 -delete
```

### Cron Schedule for Nightly Backup
Add to crontab (`crontab -e`):
```cron
0 2 * * * /opt/nexora/scripts/backup.sh >> /var/log/nexora_backup.log 2>&1
```

### Database Migration Strategy
Alembic automatically runs database migrations on container startup via `docker-compose.prod.yml`:
`alembic upgrade head`
