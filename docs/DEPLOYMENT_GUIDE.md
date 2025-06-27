# Deployment Guide - Fibonacci Trading Bot Project

## Overview
This guide provides comprehensive instructions for deploying the Fibonacci-based AI trading bot from development through production environments.

## Deployment Environments

### Environment Types
1. **Development**: Local development and testing
2. **Staging**: Pre-production testing and validation
3. **Production**: Live trading environment
4. **Disaster Recovery**: Backup production environment

### Environment Specifications

#### Development Environment
- **Purpose**: Code development and unit testing
- **Hardware**: Developer workstation (Windows 10/11)
- **MT5**: Demo account
- **Data**: Limited historical data (1-3 months)
- **Monitoring**: Basic logging
- **Backup**: Git version control

#### Staging Environment
- **Purpose**: Integration testing and strategy validation
- **Hardware**: Dedicated Windows server or VM
- **MT5**: Demo account with production-like settings
- **Data**: Full historical data (1+ years)
- **Monitoring**: Full monitoring stack
- **Backup**: Automated backups

#### Production Environment
- **Purpose**: Live trading operations
- **Hardware**: High-performance Windows server
- **MT5**: Live trading account
- **Data**: Real-time feeds + historical data
- **Monitoring**: 24/7 monitoring with alerts
- **Backup**: Real-time replication + daily backups

## Infrastructure Requirements

### Hardware Specifications

#### Minimum Requirements (Development)
- **CPU**: Intel i5 or AMD Ryzen 5 (4 cores)
- **RAM**: 16GB DDR4
- **Storage**: 500GB SSD
- **Network**: Stable broadband (10+ Mbps)
- **OS**: Windows 10/11 Professional

#### Recommended Requirements (Production)
- **CPU**: Intel i7/i9 or AMD Ryzen 7/9 (8+ cores)
- **RAM**: 32GB DDR4 or higher
- **Storage**: 1TB NVMe SSD (primary) + 2TB HDD (backup)
- **Network**: Dedicated fiber connection (100+ Mbps)
- **OS**: Windows Server 2019/2022
- **UPS**: Uninterruptible Power Supply
- **Redundancy**: Backup server for failover

### Software Dependencies

#### Core Software Stack
```
Operating System: Windows 10/11 or Windows Server 2019/2022
Python Runtime: 3.9.x or 3.10.x
MetaTrader 5: Latest stable version
Database: PostgreSQL 14+ or SQLite (development)
Web Server: Nginx (optional, for dashboard)
Process Manager: PM2 or Windows Service
Monitoring: Prometheus + Grafana (optional)
```

#### Python Dependencies
```
# Core trading dependencies
pandas>=1.5.0
numpy>=1.24.0
MetaTrader5>=5.0.45
scikit-learn>=1.2.0
tensorflow>=2.12.0

# Web and API
fastapi>=0.95.0
uvicorn>=0.22.0
websockets>=11.0

# Database and caching
sqlalchemy>=2.0.0
redis>=4.5.0

# Monitoring and logging
loguru>=0.7.0
prometheus-client>=0.16.0

# Utilities
python-dotenv>=1.0.0
pydantic>=1.10.0
click>=8.1.0
```

## Deployment Process

### Phase 1: Environment Preparation

#### Step 1.1: Server Setup
```powershell
# Windows Server Configuration
# 1. Install Windows Updates
Get-WindowsUpdate -Install -AcceptAll

# 2. Configure Windows Features
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux

# 3. Install Chocolatey (Package Manager)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# 4. Install Required Software
choco install python --version=3.10.11
choco install git
choco install postgresql
choco install redis
choco install nginx
```

#### Step 1.2: MetaTrader 5 Installation
```powershell
# Download and install MT5
$mt5Url = "https://download.mql5.com/cdn/web/metaquotes.ltd/mt5/mt5setup.exe"
$mt5Installer = "$env:TEMP\mt5setup.exe"

Invoke-WebRequest -Uri $mt5Url -OutFile $mt5Installer
Start-Process -FilePath $mt5Installer -ArgumentList "/S" -Wait

# Configure MT5 for automated trading
# Note: Manual configuration required for broker connection
```

#### Step 1.3: Database Setup
```sql
-- PostgreSQL Database Setup
CREATE DATABASE fibonacci_trading_bot;
CREATE USER trading_bot WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE fibonacci_trading_bot TO trading_bot;

-- Create required schemas
\c fibonacci_trading_bot;
CREATE SCHEMA trading;
CREATE SCHEMA analytics;
CREATE SCHEMA monitoring;
```

### Phase 2: Application Deployment

#### Step 2.1: Code Deployment
```bash
# Clone repository
git clone https://github.com/your-org/fibonacci-trading-bot.git
cd fibonacci-trading-bot

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-prod.txt

# Set up configuration
copy config\production.yaml.template config\production.yaml
# Edit configuration with production values
```

#### Step 2.2: Configuration Management
```yaml
# config/production.yaml
environment: production

mt5:
  server: "YourBroker-Live"
  login: ${MT5_LOGIN}
  password: ${MT5_PASSWORD}
  timeout: 10000

database:
  url: "postgresql://trading_bot:${DB_PASSWORD}@localhost:5432/fibonacci_trading_bot"
  pool_size: 20
  max_overflow: 30

trading:
  risk_per_trade: 0.01
  max_positions: 3
  max_daily_loss: 0.05
  
logging:
  level: INFO
  file: "C:\\TradingBot\\logs\\trading_bot.log"
  max_size: "500MB"
  backup_count: 10

monitoring:
  prometheus_port: 9090
  health_check_port: 8080
  alert_webhook: "${ALERT_WEBHOOK_URL}"
```

#### Step 2.3: Environment Variables
```powershell
# Set environment variables (Windows)
[Environment]::SetEnvironmentVariable("MT5_LOGIN", "12345678", "Machine")
[Environment]::SetEnvironmentVariable("MT5_PASSWORD", "your_password", "Machine")
[Environment]::SetEnvironmentVariable("DB_PASSWORD", "secure_db_password", "Machine")
[Environment]::SetEnvironmentVariable("ALERT_WEBHOOK_URL", "https://hooks.slack.com/...", "Machine")
[Environment]::SetEnvironmentVariable("ENVIRONMENT", "production", "Machine")
```

### Phase 3: Service Configuration

#### Step 3.1: Windows Service Setup
```python
# scripts/windows_service.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import TradingBotApplication

class TradingBotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FibonacciTradingBot"
    _svc_display_name_ = "Fibonacci Trading Bot Service"
    _svc_description_ = "Automated Fibonacci-based trading bot"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        try:
            # Initialize and run trading bot
            app = TradingBotApplication()
            asyncio.run(app.run())
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {e}")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(TradingBotService)
```

#### Step 3.2: Service Installation
```powershell
# Install Windows Service
python scripts\windows_service.py install

# Start service
python scripts\windows_service.py start

# Configure service for automatic startup
sc config FibonacciTradingBot start= auto

# Set service recovery options
sc failure FibonacciTradingBot reset= 86400 actions= restart/60000/restart/60000/restart/60000
```

### Phase 4: Monitoring Setup

#### Step 4.1: Health Check Endpoint
```python
# src/monitoring/health_check.py
from fastapi import FastAPI, HTTPException
from datetime import datetime
import psutil
from src.data.mt5_interface import mt5_interface
from src.utils.config import config

app = FastAPI(title="Trading Bot Health Check")

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "checks": {}
    }
    
    # Check MT5 connection
    try:
        if mt5_interface.connected:
            health_status["checks"]["mt5_connection"] = "healthy"
        else:
            health_status["checks"]["mt5_connection"] = "unhealthy"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["mt5_connection"] = f"error: {e}"
        health_status["status"] = "unhealthy"
    
    # Check system resources
    memory_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)
    disk_usage = psutil.disk_usage('C:\\').percent
    
    health_status["checks"]["memory_usage"] = f"{memory_usage:.1f}%"
    health_status["checks"]["cpu_usage"] = f"{cpu_usage:.1f}%"
    health_status["checks"]["disk_usage"] = f"{disk_usage:.1f}%"
    
    # Check if resources are within acceptable limits
    if memory_usage > 90 or cpu_usage > 90 or disk_usage > 90:
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics endpoint."""
    
    # Implementation for Prometheus metrics
    # This would return metrics in Prometheus format
    pass
```

#### Step 4.2: Monitoring Dashboard
```python
# src/monitoring/dashboard.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

def create_monitoring_dashboard():
    """Create Streamlit monitoring dashboard."""
    
    st.set_page_config(
        page_title="Fibonacci Trading Bot Monitor",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("🤖 Fibonacci Trading Bot Monitor")
    
    # Real-time status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("System Status", "🟢 Online", "Running")
    
    with col2:
        st.metric("Active Positions", "3", "+1")
    
    with col3:
        st.metric("Daily P&L", "$1,250.50", "+$125.30")
    
    with col4:
        st.metric("Win Rate", "68.5%", "+2.1%")
    
    # Performance charts
    st.subheader("📊 Performance Overview")
    
    # Create sample performance chart
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    cumulative_returns = pd.Series(
        index=dates,
        data=np.cumsum(np.random.normal(0.001, 0.02, len(dates)))
    )
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=cumulative_returns.index,
        y=cumulative_returns.values,
        mode='lines',
        name='Cumulative Returns',
        line=dict(color='green', width=2)
    ))
    
    fig.update_layout(
        title="Cumulative Returns",
        xaxis_title="Date",
        yaxis_title="Returns (%)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    create_monitoring_dashboard()
```

### Phase 5: Security Configuration

#### Step 5.1: Security Hardening
```powershell
# Windows Security Configuration

# 1. Configure Windows Firewall
New-NetFirewallRule -DisplayName "Trading Bot API" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
New-NetFirewallRule -DisplayName "Health Check" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow

# 2. Disable unnecessary services
Stop-Service -Name "Themes" -Force
Set-Service -Name "Themes" -StartupType Disabled

# 3. Configure automatic updates
Install-Module PSWindowsUpdate
Get-WindowsUpdate -Install -AcceptAll -AutoReboot

# 4. Set up user accounts
$SecurePassword = ConvertTo-SecureString "ComplexPassword123!" -AsPlainText -Force
New-LocalUser -Name "TradingBotUser" -Password $SecurePassword -Description "Trading Bot Service Account"
Add-LocalGroupMember -Group "Users" -Member "TradingBotUser"
```

#### Step 5.2: SSL/TLS Configuration
```nginx
# nginx.conf for HTTPS dashboard access
server {
    listen 443 ssl;
    server_name trading-bot.yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        proxy_pass http://localhost:8080/health;
    }
}
```

## Backup and Recovery

### Backup Strategy

#### Automated Backup Script
```powershell
# scripts/backup.ps1
param(
    [string]$BackupPath = "D:\Backups\TradingBot",
    [int]$RetentionDays = 30
)

$Date = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$BackupDir = Join-Path $BackupPath $Date

# Create backup directory
New-Item -ItemType Directory -Path $BackupDir -Force

# Backup configuration files
Copy-Item -Path "C:\TradingBot\config\*" -Destination "$BackupDir\config" -Recurse -Force

# Backup logs (last 7 days)
$LogFiles = Get-ChildItem -Path "C:\TradingBot\logs" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) }
Copy-Item -Path $LogFiles.FullName -Destination "$BackupDir\logs" -Force

# Backup database
pg_dump -h localhost -U trading_bot -d fibonacci_trading_bot > "$BackupDir\database_backup.sql"

# Backup ML models
Copy-Item -Path "C:\TradingBot\data\models\*" -Destination "$BackupDir\models" -Recurse -Force

# Cleanup old backups
Get-ChildItem -Path $BackupPath | Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$RetentionDays) } | Remove-Item -Recurse -Force

Write-Host "Backup completed: $BackupDir"
```

#### Scheduled Backup Task
```powershell
# Create scheduled task for daily backups
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\TradingBot\scripts\backup.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "TradingBotBackup" -Action $Action -Trigger $Trigger -Settings $Settings -User "SYSTEM"
```

### Disaster Recovery

#### Recovery Procedures
1. **System Failure Recovery**
   - Restore from latest system backup
   - Reinstall MT5 and configure broker connection
   - Restore application from backup
   - Verify all services are running

2. **Data Corruption Recovery**
   - Stop trading bot service
   - Restore database from latest backup
   - Restore ML models from backup
   - Restart services and verify data integrity

3. **Network Connectivity Issues**
   - Implement automatic reconnection logic
   - Use backup internet connection if available
   - Alert administrators of connectivity issues
   - Log all connection events for analysis

## Deployment Checklist

### Pre-Deployment Checklist
- [ ] All tests pass in staging environment
- [ ] Performance benchmarks met
- [ ] Security scan completed
- [ ] Backup procedures tested
- [ ] Monitoring systems configured
- [ ] Documentation updated
- [ ] Rollback plan prepared

### Deployment Checklist
- [ ] Code deployed to production server
- [ ] Configuration files updated
- [ ] Environment variables set
- [ ] Database migrations applied
- [ ] Services installed and started
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] SSL certificates installed

### Post-Deployment Checklist
- [ ] System functionality verified
- [ ] Trading operations tested
- [ ] Performance monitoring active
- [ ] Backup systems operational
- [ ] Alert systems tested
- [ ] Documentation updated
- [ ] Team notified of deployment

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
- [ ] Check system health status
- [ ] Review trading performance
- [ ] Monitor resource usage
- [ ] Verify backup completion
- [ ] Check for alerts or errors

#### Weekly Tasks
- [ ] Review and analyze trading logs
- [ ] Update market data
- [ ] Performance optimization review
- [ ] Security updates check
- [ ] Backup verification

#### Monthly Tasks
- [ ] Full system performance review
- [ ] ML model retraining evaluation
- [ ] Security audit
- [ ] Disaster recovery test
- [ ] Documentation updates

### Troubleshooting Guide

#### Common Issues and Solutions

1. **MT5 Connection Lost**
   ```
   Symptoms: Trading stops, connection errors in logs
   Solution: Restart MT5 service, check network connectivity
   Prevention: Implement connection monitoring and auto-reconnect
   ```

2. **High Memory Usage**
   ```
   Symptoms: System slowdown, memory alerts
   Solution: Restart trading bot service, check for memory leaks
   Prevention: Regular memory profiling, optimize data structures
   ```

3. **Database Connection Issues**
   ```
   Symptoms: Data not saving, database errors
   Solution: Restart database service, check connection pool
   Prevention: Monitor database performance, optimize queries
   ```

This deployment guide provides a comprehensive framework for deploying the trading bot across different environments while ensuring security, reliability, and maintainability.
