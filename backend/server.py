from fastapi import FastAPI, APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from enum import Enum
import json

# Automation imports
import requests
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from faker import Faker
from fake_useragent import UserAgent
import re
import zipfile
import shutil
from pathlib import Path
import tempfile

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global automation state
automation_state = {
    "is_running": False,
    "total_accounts": 0,
    "successful_accounts": 0,
    "failed_accounts": 0,
    "current_batch": 0,
    "last_cooldown": None,
    "errors": [],
    "task": None
}

fake = Faker()
ua = UserAgent()

# Models
class AutomationStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    COOLDOWN = "cooldown"
    ERROR = "error"

class AccountLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    temp_email_id: str
    status: str  # created, email_verified, failed
    error_message: Optional[str] = None
    verification_token: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None

class AutomationStats(BaseModel):
    is_running: bool
    status: AutomationStatus
    total_accounts: int
    successful_accounts: int
    failed_accounts: int
    current_batch: int
    last_cooldown: Optional[datetime]
    errors: List[str]

class GuerrillaMailService:
    BASE_URL = "https://www.guerrillamail.com/ajax.php"
    
    @staticmethod
    def get_email_address():
        """Get a temporary email address"""
        try:
            params = {
                'f': 'get_email_address',
                'lang': 'en'
            }
            response = requests.get(GuerrillaMailService.BASE_URL, params=params)
            data = response.json()
            return {
                'email': data.get('email_addr'),
                'sid_token': data.get('sid_token'),
                'email_id': data.get('alias')
            }
        except Exception as e:
            logging.error(f"Error getting email address: {e}")
            return None
    
    @staticmethod
    def check_email(sid_token, seq=0):
        """Check for new emails"""
        try:
            params = {
                'f': 'check_email',
                'sid_token': sid_token,
                'seq': seq
            }
            response = requests.get(GuerrillaMailService.BASE_URL, params=params)
            data = response.json()
            return data.get('list', [])
        except Exception as e:
            logging.error(f"Error checking email: {e}")
            return []
    
    @staticmethod
    def get_email_content(sid_token, email_id):
        """Get email content"""
        try:
            params = {
                'f': 'fetch_email',
                'sid_token': sid_token,
                'email_id': email_id
            }
            response = requests.get(GuerrillaMailService.BASE_URL, params=params)
            data = response.json()
            return data.get('mail_body', '')
        except Exception as e:
            logging.error(f"Error getting email content: {e}")
            return ''

class AutomationService:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={ua.random}")
        chrome_options.binary_location = "/usr/bin/chromium"
        
        service = Service("/usr/bin/chromedriver")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def generate_user_data(self):
        """Generate realistic user data"""
        username = fake.user_name() + str(random.randint(100, 999))
        password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        return {
            'username': username,
            'password': password
        }
    
    async def create_account(self):
        """Create a single account"""
        try:
            # Get temporary email
            email_data = GuerrillaMailService.get_email_address()
            if not email_data:
                raise Exception("Failed to get temporary email")
            
            # Generate user data  
            user_data = self.generate_user_data()
            user_data['email'] = email_data['email']
            
            # Setup browser
            self.setup_driver()
            
            # Navigate to signup page
            self.driver.get("https://steep.gg/")
            await asyncio.sleep(2)
            
            # Fill the form
            username_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            username_field.clear()
            username_field.send_keys(user_data['username'])
            
            email_field = self.driver.find_element(By.ID, "email")
            email_field.clear()
            email_field.send_keys(user_data['email'])
            
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(user_data['password'])
            
            confirm_password_field = self.driver.find_element(By.ID, "confirm-password")
            confirm_password_field.clear()
            confirm_password_field.send_keys(user_data['password'])
            
            # Fill referral code - use the correct ID found in analysis
            try:
                referral_field = self.driver.find_element(By.ID, "referral")
                referral_field.clear()
                referral_field.send_keys("Cook")
                logging.info("✅ Successfully filled referral code 'Cook'")
            except Exception as e:
                logging.warning(f"Could not find referral code field: {e}")
            
            # Submit the form
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(., 'Join Waitlist')]")
            submit_button.click()
            
            await asyncio.sleep(3)
            
            # Save account log
            account_log = AccountLog(
                username=user_data['username'],
                email=user_data['email'],
                temp_email_id=email_data['sid_token'],
                status="created"
            )
            
            await db.account_logs.insert_one(account_log.dict())
            
            # Wait for verification email and process it
            verification_success = await self.process_verification_email(
                email_data['sid_token'], 
                account_log.id
            )
            
            if verification_success:
                automation_state["successful_accounts"] += 1
                return {"success": True, "account": user_data['username']}
            else:
                automation_state["failed_accounts"] += 1
                return {"success": False, "error": "Email verification failed"}
                
        except Exception as e:
            automation_state["failed_accounts"] += 1
            error_msg = f"Account creation failed: {str(e)}"
            automation_state["errors"].append(error_msg)
            logging.error(error_msg)
            return {"success": False, "error": error_msg}
        finally:
            if self.driver:
                self.driver.quit()
    
    async def process_verification_email(self, sid_token, account_id, max_attempts=30):
        """Process email verification"""
        try:
            for attempt in range(max_attempts):
                await asyncio.sleep(10)  # Wait 10 seconds between checks
                
                emails = GuerrillaMailService.check_email(sid_token)
                
                for email in emails:
                    if 'steep.gg' in email.get('mail_from', '').lower():
                        # Get email content
                        email_content = GuerrillaMailService.get_email_content(sid_token, email['mail_id'])
                        
                        # Extract verification link
                        verification_link = self.extract_verification_link(email_content)
                        
                        if verification_link:
                            # Click verification link
                            success = await self.click_verification_link(verification_link)
                            
                            if success:
                                # Update account status
                                await db.account_logs.update_one(
                                    {"id": account_id},
                                    {"$set": {
                                        "status": "email_verified", 
                                        "verified_at": datetime.now(timezone.utc),
                                        "verification_token": verification_link
                                    }}
                                )
                                return True
                            
            return False
        except Exception as e:
            logging.error(f"Email verification failed: {e}")
            return False
    
    def extract_verification_link(self, email_content):
        """Extract verification link from email"""
        try:
            # Look for steep.gg verification link pattern
            pattern = r'https://steep\.gg/verify-email\?token=([a-zA-Z0-9]+)'
            match = re.search(pattern, email_content)
            
            if match:
                return match.group(0)
            
            # Alternative pattern search
            pattern2 = r'href="(https://steep\.gg/verify-email[^"]*)"'
            match2 = re.search(pattern2, email_content)
            
            if match2:
                return match2.group(1)
                
            return None
        except Exception as e:
            logging.error(f"Error extracting verification link: {e}")
            return None
    
    async def click_verification_link(self, verification_link):
        """Click the verification link"""
        try:
            # Setup new browser session for verification
            self.setup_driver()
            self.driver.get(verification_link)
            await asyncio.sleep(5)
            
            # Check if verification was successful
            page_source = self.driver.page_source.lower()
            success_indicators = ['verified', 'success', 'confirmed', 'welcome']
            
            is_success = any(indicator in page_source for indicator in success_indicators)
            
            return is_success
        except Exception as e:
            logging.error(f"Error clicking verification link: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

# Global automation service instance
automation_service = AutomationService()

async def automation_worker():
    """Background worker for automation"""
    while automation_state["is_running"]:
        try:
            # Check if we need to cooldown
            if automation_state["current_batch"] >= 15:
                automation_state["last_cooldown"] = datetime.now(timezone.utc)
                logging.info("Starting 15-minute cooldown...")
                await asyncio.sleep(15 * 60)  # 15 minutes
                automation_state["current_batch"] = 0
                automation_state["last_cooldown"] = None
                logging.info("Cooldown complete, resuming automation...")
            
            # Create account
            result = await automation_service.create_account()
            automation_state["total_accounts"] += 1
            automation_state["current_batch"] += 1
            
            if result["success"]:
                logging.info(f"Successfully created account: {result['account']}")
            else:
                logging.error(f"Failed to create account: {result['error']}")
            
            # Random delay between accounts (1-3 minutes)
            delay = random.randint(60, 180)
            await asyncio.sleep(delay)
            
        except Exception as e:
            error_msg = f"Automation worker error: {str(e)}"
            automation_state["errors"].append(error_msg)
            logging.error(error_msg)
            await asyncio.sleep(60)  # Wait 1 minute before retrying

# API Routes
@api_router.post("/automation/start")
async def start_automation(background_tasks: BackgroundTasks):
    """Start the automation process"""
    if automation_state["is_running"]:
        raise HTTPException(status_code=400, detail="Automation is already running")
    
    automation_state["is_running"] = True
    automation_state["errors"] = []
    
    # Start background task
    background_tasks.add_task(automation_worker)
    
    return {"message": "Automation started successfully"}

@api_router.post("/automation/stop")
async def stop_automation():
    """Stop the automation process"""
    automation_state["is_running"] = False
    return {"message": "Automation stopped successfully"}

@api_router.get("/automation/status", response_model=AutomationStats)
async def get_automation_status():
    """Get current automation status"""
    status = AutomationStatus.STOPPED
    if automation_state["is_running"]:
        if automation_state["last_cooldown"]:
            status = AutomationStatus.COOLDOWN
        else:
            status = AutomationStatus.RUNNING
    
    return AutomationStats(
        is_running=automation_state["is_running"],
        status=status,
        total_accounts=automation_state["total_accounts"],
        successful_accounts=automation_state["successful_accounts"],
        failed_accounts=automation_state["failed_accounts"],
        current_batch=automation_state["current_batch"],
        last_cooldown=automation_state["last_cooldown"],
        errors=automation_state["errors"][-10:]  # Last 10 errors
    )

@api_router.get("/automation/logs", response_model=List[AccountLog])
async def get_automation_logs(limit: int = 50):
    """Get recent automation logs"""
    logs = await db.account_logs.find().sort("created_at", -1).limit(limit).to_list(limit)
    return [AccountLog(**log) for log in logs]

@api_router.delete("/automation/logs")
async def clear_automation_logs():
    """Clear all automation logs"""
    result = await db.account_logs.delete_many({})
    return {"message": f"Cleared {result.deleted_count} log entries"}

@api_router.post("/automation/reset")
async def reset_automation_stats():
    """Reset automation statistics"""
    automation_state.update({
        "total_accounts": 0,
        "successful_accounts": 0,
        "failed_accounts": 0,
        "current_batch": 0,
        "last_cooldown": None,
        "errors": []
    })
    return {"message": "Automation statistics reset successfully"}

@api_router.get("/download/source")
async def download_source_code():
    """Download the complete source code as a ZIP file"""
    try:
        # Create a temporary directory for the ZIP file
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "steep-automation-source.zip"
            
            # Create ZIP file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add backend files
                backend_dir = Path("/app/backend")
                for file_path in backend_dir.rglob("*"):
                    if file_path.is_file() and not any(skip in str(file_path) for skip in ['.git', '__pycache__', '.pyc', 'node_modules', '.env']):
                        arcname = f"backend/{file_path.relative_to(backend_dir)}"
                        zipf.write(file_path, arcname)
                
                # Add frontend files
                frontend_dir = Path("/app/frontend")
                for file_path in frontend_dir.rglob("*"):
                    if file_path.is_file() and not any(skip in str(file_path) for skip in ['.git', '__pycache__', '.pyc', 'node_modules', 'build']):
                        arcname = f"frontend/{file_path.relative_to(frontend_dir)}"
                        zipf.write(file_path, arcname)
                
                # Add root files
                root_files = [
                    "/app/README.md",
                ]
                
                for root_file in root_files:
                    if Path(root_file).exists():
                        zipf.write(root_file, Path(root_file).name)
                
                # Add deployment files
                deployment_content = {
                    "ecosystem.config.js": '''module.exports = {
  apps: [{
    name: 'steep-backend',
    cwd: './backend',
    script: 'venv/bin/uvicorn',
    args: 'server:app --host 0.0.0.0 --port 8001',
    env: {
      NODE_ENV: 'production'
    }
  }, {
    name: 'steep-frontend',
    cwd: './frontend',
    script: 'npx',
    args: 'serve -s build -l 3000',
    env: {
      NODE_ENV: 'production'
    }
  }]
}''',
                    "docker-compose.yml": '''version: '3.8'
services:
  mongodb:
    image: mongo:7.0
    restart: unless-stopped
    environment:
      MONGO_INITDB_DATABASE: steep_automation
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"
  
  backend:
    build: ./backend
    restart: unless-stopped
    depends_on:
      - mongodb
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=steep_automation
    ports:
      - "8001:8001"
    volumes:
      - /dev/shm:/dev/shm  # Required for Chrome
  
  frontend:
    build: ./frontend
    restart: unless-stopped
    depends_on:
      - backend
    ports:
      - "3000:3000"

volumes:
  mongodb_data:''',
                    "backend/Dockerfile": '''FROM python:3.11-slim

# Install system dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y \\
    chromium \\
    chromium-driver \\
    xvfb \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]''',
                    "frontend/Dockerfile": '''FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]''',
                    "DEPLOYMENT.md": '''# Steep.gg Automation Tool - Deployment Guide

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
'''
                }
                
                # Add deployment files to ZIP
                for filename, content in deployment_content.items():
                    zipf.writestr(filename, content)
            
            # Copy the ZIP file to a permanent location
            permanent_zip = Path("/tmp/steep-automation-source.zip")
            shutil.copy2(zip_path, permanent_zip)
            
            return FileResponse(
                path=permanent_zip,
                filename="steep-automation-source.zip",
                media_type="application/zip"
            )
    
    except Exception as e:
        logging.error(f"Error creating source code ZIP: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()