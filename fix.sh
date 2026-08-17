# Stop the service
sudo systemctl stop ai-news-bot

# Get paths
PROJECT_DIR="/home/pi5/Documents/ai-news-bot"
PYTHON_PATH=$(cd "$PROJECT_DIR" && poetry run which python)

echo "Python path: $PYTHON_PATH"

# Create fixed wrapper script
cat > "$PROJECT_DIR/run_bot.sh" <<EOF
#!/bin/bash
cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"
export PYTHONUNBUFFERED=1
exec "$PYTHON_PATH" -m ai_news_bot.main
EOF

chmod +x "$PROJECT_DIR/run_bot.sh"

# Test the wrapper
echo "Testing wrapper script..."
cd "$PROJECT_DIR"
timeout 10s ./run_bot.sh || echo "Test completed (or timed out - this is expected)"

# Update systemd service with better environment
sudo tee /etc/systemd/system/ai-news-bot.service <<EOF
[Unit]
Description=AI News Aggregator Bot
After=network.target

[Service]
Type=simple
User=pi5
Group=pi5
WorkingDirectory=$PROJECT_DIR
Environment=PATH=/home/pi5/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$PROJECT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$PROJECT_DIR/run_bot.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload and start
sudo systemctl daemon-reload
sudo systemctl start ai-news-bot

# Check status
sleep 5
sudo systemctl status ai-news-bot
