# Steep.gg Automation Tool - Deployment Guide

## Quick Setup Options

### Option 1: Docker Compose (Recommended)
```bash
git clone <your-repo>
cd steep-automation-tool
docker-compose up -d
```

### Option 2: Manual Setup

#### Prerequisites
- Ubuntu 22.04 LTS
- Node.js 20+
- Python 3.11+
- MongoDB 7.0
- Chrome/Chromium

#### Installation Steps
1. Install dependencies:
```bash
sudo apt update
sudo apt install -y nodejs npm python3.11 python3.11-venv chromium chromium-driver mongodb-org nginx
```

2. Setup Backend:
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Setup Frontend:
```bash
cd frontend
npm install
npm run build
```

4. Configure Environment:
```bash
# Backend .env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="steep_automation"
CORS_ORIGINS="*"
```

5. Start Services:
```bash
npm install -g pm2
pm2 start ecosystem.config.js
```

6. Configure Nginx (optional):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
    }
}
```

## Features
- Automated account creation on steep.gg
- Email verification using GuerrillaMail
- Rate limiting (15 accounts per batch)
- Real-time monitoring dashboard
- MongoDB logging and persistence

## Usage
1. Access the dashboard at http://localhost:3000
2. Click "Start Automation" to begin
3. Monitor progress in real-time
4. System automatically handles rate limiting

## Troubleshooting
- Ensure Chrome/Chromium is installed for Selenium
- Check MongoDB connection
- Verify all environment variables are set
- Monitor logs with: pm2 logs
