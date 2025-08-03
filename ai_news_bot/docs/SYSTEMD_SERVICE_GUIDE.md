# 🚀 Systemd Service Setup Guide

This guide explains how to run the AI News Aggregator Bot as a systemd service for automatic startup, monitoring, and management.

## 🔧 Quick Setup

### 1. Run the Setup Script

```bash
# Make the setup script executable
chmod +x setup_systemd_service.sh

# Run the setup (requires sudo for service creation)
./setup_systemd_service.sh
```

### 2. Configure Environment

```bash
# Edit your .env file (if not already configured)
nano .env

# Ensure these are set:
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel
SUMMARIZER_TYPE=local  # or openai/deepseek
```

### 3. Start the Service

```bash
# Enable auto-start on boot
sudo systemctl enable ai-news-bot

# Start the service
sudo systemctl start ai-news-bot

# Check status
sudo systemctl status ai-news-bot
```

## 🎮 Service Management

### Using the Management Script

The setup creates a convenient management script:

```bash
# Start the service
./manage_service.sh start

# Stop the service
./manage_service.sh stop

# Restart the service
./manage_service.sh restart

# Check status
./manage_service.sh status

# View recent logs
./manage_service.sh logs

# Follow logs in real-time
./manage_service.sh tail

# Enable auto-start
./manage_service.sh enable

# Disable auto-start
./manage_service.sh disable

# Update dependencies and restart
./manage_service.sh update
```

### Direct Systemctl Commands

```bash
# Service control
sudo systemctl start ai-news-bot
sudo systemctl stop ai-news-bot
sudo systemctl restart ai-news-bot
sudo systemctl reload ai-news-bot

# Status and information
sudo systemctl status ai-news-bot
sudo systemctl is-active ai-news-bot
sudo systemctl is-enabled ai-news-bot

# Enable/disable auto-start
sudo systemctl enable ai-news-bot
sudo systemctl disable ai-news-bot

# View logs
sudo journalctl -u ai-news-bot
sudo journalctl -u ai-news-bot -f  # Follow logs
sudo journalctl -u ai-news-bot --since "1 hour ago"
sudo journalctl -u ai-news-bot --since "2025-01-01"
```

## 📊 Monitoring

### Built-in Monitoring Script

```bash
# Run system monitor
./monitor_bot.sh

# Output example:
# === AI News Bot Monitor ===
# Time: Mon Jan 15 10:30:00 2025
# 
# 🤖 Service Status:
#   ✅ Service: RUNNING
#   ✅ Auto-start: ENABLED
# 
# 💻 System Resources:
#   Memory: 2.1/8.0 GB (26%)
#   CPU: 15.2% usage
#   Temperature: 45°C
# 
# 📊 Recent Activity (last 24h):
#   Articles processed: 48
#   Errors: 0
```

### Log Analysis

```bash
# Check for errors
sudo journalctl -u ai-news-bot | grep -i error

# Count processed articles today
sudo journalctl -u ai-news-bot --since today | grep -c "Successfully generated summary"

# Monitor memory usage
sudo journalctl -u ai-news-bot | grep -i memory

# Check SSL issues
sudo journalctl -u ai-news-bot | grep -i ssl
```

### Performance Monitoring

```bash
# Monitor resource usage
top -p $(pgrep -f ai-news-bot)

# Memory usage details
cat /proc/$(pgrep -f ai-news-bot)/status | grep -E "(VmSize|VmRSS|VmData)"

# Check service restart count
systemctl show ai-news-bot --property=NRestarts
```

## 🔐 Security Features

The systemd service includes security hardening:

- **NoNewPrivileges**: Prevents privilege escalation
- **PrivateTmp**: Isolated temporary directory
- **ProtectSystem**: Read-only access to system directories
- **ProtectHome**: No access to user home directories
- **Resource Limits**: Memory and CPU quotas

## 📁 File Locations

After setup, you'll have these files:

```
/etc/systemd/system/ai-news-bot.service    # Service definition
/etc/logrotate.d/ai-news-bot               # Log rotation config
./manage_service.sh                        # Management script
./monitor_bot.sh                           # Monitoring script
./logs/                                    # Application logs
./data/                                    # Database files
```

## 🔄 Auto-restart Configuration

The service is configured to:
- **Restart on failure** with 10-second delay
- **Restart on crash** automatically
- **Limit restart attempts** to prevent boot loops
- **Start after network** is available

## 📝 Log Management

### Log Rotation

Logs are automatically rotated:
- **Daily rotation**
- **Keep 7 days** of logs
- **Compress old logs**
- **Automatic cleanup**

### Log Locations

```bash
# Application logs
tail -f logs/app.log

# Systemd logs
sudo journalctl -u ai-news-bot -f

# All logs combined
sudo journalctl -u ai-news-bot --output=short-precise
```

## 🚨 Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status ai-news-bot

# Check configuration
sudo systemctl cat ai-news-bot

# Validate environment
poetry run python -c "from ai_news_bot.config import load_config; print('Config OK')"

# Test manually
poetry run ai-news-bot
```

### Common Issues

#### 1. **Permission Errors**
```bash
# Fix file permissions
chmod +x ./manage_service.sh ./monitor_bot.sh
chown $USER:$USER -R logs/ data/ models/
```

#### 2. **Environment Variables Not Loading**
```bash
# Check .env file exists and is readable
ls -la .env
cat .env

# Test configuration loading
poetry run python -c "
from ai_news_bot.config import load_config
config = load_config()
print(f'Bot token: {config.telegram_bot_token[:10]}...')
print(f'Channel: {config.telegram_channel_id}')
"
```

#### 3. **Memory Issues**
```bash
# Check memory usage
./monitor_bot.sh

# Adjust memory limits in service file
sudo systemctl edit ai-news-bot

# Add:
# [Service]
# MemoryMax=4G
```

#### 4. **Network Issues**
```bash
# Test connectivity
poetry run python test_connectivity.py

# Check SSL configuration
grep SSL_VERIFY .env
```

### Reset Service

If you need to completely reset the service:

```bash
# Stop and disable
sudo systemctl stop ai-news-bot
sudo systemctl disable ai-news-bot

# Remove service files
sudo rm /etc/systemd/system/ai-news-bot.service
sudo rm /etc/logrotate.d/ai-news-bot

# Reload systemd
sudo systemctl daemon-reload

# Re-run setup
./setup_systemd_service.sh
```

## 🔄 Updates and Maintenance

### Updating the Bot

```bash
# Option 1: Use management script
./manage_service.sh update

# Option 2: Manual update
git pull                    # If using git
poetry install --no-dev    # Update dependencies
sudo systemctl restart ai-news-bot
```

### Backup Configuration

```bash
# Backup important files
tar -czf ai-news-bot-backup.tar.gz .env logs/ data/

# Restore from backup
tar -xzf ai-news-bot-backup.tar.gz
```

### Health Checks

Set up a cron job for automated health checks:

```bash
# Add to crontab
echo "*/15 * * * * $PWD/monitor_bot.sh >> /tmp/ai-news-bot-health.log 2>&1" | crontab -

# Or create a health check service
sudo tee /etc/systemd/system/ai-news-bot-health.service > /dev/null <<EOF
[Unit]
Description=AI News Bot Health Check
Requires=ai-news-bot.service

[Service]
Type=oneshot
ExecStart=$PWD/monitor_bot.sh
User=$USER

[Install]
WantedBy=multi-user.target
EOF

# Timer for health checks
sudo tee /etc/systemd/system/ai-news-bot-health.timer > /dev/null <<EOF
[Unit]
Description=Run AI News Bot Health Check
Requires=ai-news-bot-health.service

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl enable ai-news-bot-health.timer
sudo systemctl start ai-news-bot-health.timer
```

## 🎯 Best Practices

1. **Monitor regularly** with `./monitor_bot.sh`
2. **Check logs** daily with `./manage_service.sh logs`
3. **Update dependencies** weekly with `./manage_service.sh update`
4. **Backup configuration** before major changes
5. **Test after updates** to ensure everything works
6. **Monitor resource usage** on Raspberry Pi
7. **Keep SSL certificates updated**

This systemd service setup provides a robust, production-ready deployment of your AI News Aggregator Bot with comprehensive monitoring and management capabilities! 🚀