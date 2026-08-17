# Step 1: Get the correct paths
PROJECT_DIR=$(pwd)
VENV_PATH=$(poetry env info --path)
PYTHON_PATH=$(poetry run which python)

echo "Project: $PROJECT_DIR"
echo "Venv: $VENV_PATH" 
echo "Python: $PYTHON_PATH"

# Step 2: Create a simple wrapper script
cat > run_bot.sh <<EOF
#!/bin/bash
cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"
poetry run python -m ai_news_bot.main
EOF

chmod +x run_bot.sh

# Step 3: Update the service file with the wrapper
sudo tee /etc/systemd/system/ai-news-bot.service <<EOF
[Unit]
Description=AI News Aggregator Bot
After=network.target

[Service]
Type=simple
User=pi5
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/run_bot.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Step 4: Reload and start
sudo systemctl daemon-reload
sudo systemctl start ai-news-bot
sudo systemctl status ai-news-bot
