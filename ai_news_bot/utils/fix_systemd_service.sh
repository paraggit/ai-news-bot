#!/bin/bash

# Fix systemd service for AI News Aggregator Bot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

PROJECT_DIR="$(pwd)"
USER="$(whoami)"
SERVICE_NAME="ai-news-bot"

print_step "Fixing AI News Bot systemd service..."

# Stop the service first
print_step "Stopping current service..."
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# Get correct paths
print_step "Detecting correct paths..."

# Get Poetry virtual environment info
VENV_PATH=$(poetry env info --path 2>/dev/null)
if [[ -z "$VENV_PATH" ]]; then
    print_error "Could not detect Poetry virtual environment"
    print_status "Creating virtual environment..."
    poetry install --only=main
    VENV_PATH=$(poetry env info --path)
fi

PYTHON_PATH="$VENV_PATH/bin/python"

print_status "Project directory: $PROJECT_DIR"
print_status "Virtual environment: $VENV_PATH"
print_status "Python executable: $PYTHON_PATH"

# Verify paths exist
if [[ ! -f "$PYTHON_PATH" ]]; then
    print_error "Python executable not found at: $PYTHON_PATH"
    print_status "Trying alternative detection..."
    
    # Alternative: use poetry run which python
    ALT_PYTHON=$(poetry run which python 2>/dev/null)
    if [[ -n "$ALT_PYTHON" ]]; then
        PYTHON_PATH="$ALT_PYTHON"
        print_status "Found Python at: $PYTHON_PATH"
    else
        print_error "Could not locate Python executable"
        exit 1
    fi
fi

# Verify the module can be imported
print_step "Testing module import..."
if "$PYTHON_PATH" -c "import ai_news_bot.main" 2>/dev/null; then
    print_status "Module import successful"
else
    print_error "Cannot import ai_news_bot.main"
    print_status "Installing dependencies..."
    poetry install --only=main
    
    # Test again
    if "$PYTHON_PATH" -c "import ai_news_bot.main" 2>/dev/null; then
        print_status "Module import successful after install"
    else
        print_error "Module import still failing"
        exit 1
    fi
fi

# Create corrected service file
print_step "Creating corrected service file..."

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=AI News Aggregator Bot
Documentation=https://github.com/yourusername/ai-news-aggregator
After=network.target network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$PROJECT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$PYTHON_PATH -m ai_news_bot.main
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=15
StartLimitBurst=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-news-bot

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Resource limits
MemoryMax=2G
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

print_status "Service file updated"

# Create a test script to verify the service command works
print_step "Creating test script..."
TEST_SCRIPT="$PROJECT_DIR/test_service_command.sh"

cat > "$TEST_SCRIPT" <<EOF
#!/bin/bash
cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"
export PYTHONUNBUFFERED=1
exec "$PYTHON_PATH" -m ai_news_bot.main
EOF

chmod +x "$TEST_SCRIPT"

# Test the command manually
print_step "Testing service command..."
echo "Testing: $PYTHON_PATH -m ai_news_bot.main"

# Create a wrapper script that sets up the environment properly
WRAPPER_SCRIPT="$PROJECT_DIR/run_bot.sh"
cat > "$WRAPPER_SCRIPT" <<EOF
#!/bin/bash
cd "$PROJECT_DIR"
export PYTHONPATH="$PROJECT_DIR"
export PYTHONUNBUFFERED=1
exec "$PYTHON_PATH" -m ai_news_bot.main "\$@"
EOF

chmod +x "$WRAPPER_SCRIPT"

# Update service to use wrapper script
print_step "Updating service to use wrapper script..."

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=AI News Aggregator Bot
Documentation=https://github.com/yourusername/ai-news-aggregator
After=network.target network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$WRAPPER_SCRIPT
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=15
StartLimitBurst=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-news-bot

# Security settings (relaxed for troubleshooting)
NoNewPrivileges=true
PrivateTmp=false
ProtectSystem=false
ProtectHome=false

# Resource limits
MemoryMax=2G
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and test
print_step "Reloading systemd configuration..."
sudo systemctl daemon-reload

print_step "Testing service start..."
if sudo systemctl start "$SERVICE_NAME"; then
    print_status "Service started successfully!"
    
    # Wait a moment and check status
    sleep 3
    
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "✅ Service is running!"
        
        # Show status
        echo ""
        print_step "Service status:"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
        
        echo ""
        print_step "Recent logs:"
        sudo journalctl -u "$SERVICE_NAME" --no-pager -l -n 10
    else
        print_error "Service started but is not active"
        sudo systemctl status "$SERVICE_NAME" --no-pager -l
    fi
else
    print_error "Failed to start service"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
fi

echo ""
print_status "🔧 Troubleshooting commands:"
echo "sudo systemctl status $SERVICE_NAME"
echo "sudo journalctl -u $SERVICE_NAME -f"
echo "$WRAPPER_SCRIPT  # Test manually"
echo ""
print_status "Service file location: $SERVICE_FILE"
print_status "Wrapper script: $WRAPPER_SCRIPT"