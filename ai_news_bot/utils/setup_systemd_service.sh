#!/bin/bash

# AI News Aggregator Bot - Systemd Service Setup Script
# This script sets up the bot to run as a systemd service with auto-restart

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Get script directory and project path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$SCRIPT_DIR"
USER=$(whoami)
SERVICE_NAME="ai-news-bot"

print_step "Setting up AI News Aggregator Bot as systemd service..."
print_status "Project directory: $PROJECT_DIR"
print_status "User: $USER"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root!"
    print_status "Run as regular user with sudo access"
    exit 1
fi

# Check if project files exist
check_project_files() {
    print_step "Checking project files..."
    
    if [[ ! -f "$PROJECT_DIR/pyproject.toml" ]]; then
        print_error "pyproject.toml not found. Are you in the project directory?"
        exit 1
    fi
    
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        print_warning ".env file not found. Make sure to configure it before starting the service."
    fi
    
    print_status "Project files found"
}

# Check if Poetry is installed
check_poetry() {
    print_step "Checking Poetry installation..."
    
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry not found. Please install Poetry first."
        print_status "Install with: curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
    
    POETRY_PATH=$(which poetry)
    print_status "Poetry found at: $POETRY_PATH"
}

# Install dependencies
install_dependencies() {
    print_step "Installing project dependencies..."
    
    cd "$PROJECT_DIR"
    poetry install --no-dev
    
    print_status "Dependencies installed"
}

# Create systemd service file
create_service_file() {
    print_step "Creating systemd service file..."
    
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    # Get Python virtual environment path
    VENV_PATH=$(poetry env info --path)
    PYTHON_PATH="$VENV_PATH/bin/python"
    
    print_status "Virtual environment: $VENV_PATH"
    print_status "Python executable: $PYTHON_PATH"
    
    # Create the service file
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
RestartSec=10
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

    print_status "Service file created at: $SERVICE_FILE"
}

# Create log rotation configuration
create_logrotate_config() {
    print_step "Setting up log rotation..."
    
    LOGROTATE_FILE="/etc/logrotate.d/${SERVICE_NAME}"
    
    sudo tee "$LOGROTATE_FILE" > /dev/null <<EOF
$PROJECT_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload $SERVICE_NAME 2>/dev/null || true
    endscript
}
EOF

    print_status "Log rotation configured at: $LOGROTATE_FILE"
}

# Create environment file template
create_env_template() {
    print_step "Checking environment configuration..."
    
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        print_warning "Creating .env template from .env.example"
        
        if [[ -f "$PROJECT_DIR/.env.example" ]]; then
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
            print_status ".env file created from template"
            print_warning "Please edit .env file with your configuration before starting the service!"
        else
            print_error ".env.example not found. Please create .env file manually."
        fi
    else
        print_status ".env file already exists"
    fi
}

# Create directories
create_directories() {
    print_step "Creating necessary directories..."
    
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/data"
    mkdir -p "$PROJECT_DIR/models"
    
    # Set proper permissions
    chmod 755 "$PROJECT_DIR/logs"
    chmod 755 "$PROJECT_DIR/data"
    chmod 755 "$PROJECT_DIR/models"
    
    print_status "Directories created with proper permissions"
}

# Test the service
test_service() {
    print_step "Testing service configuration..."
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Check service status
    if sudo systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
        print_status "Service is already enabled"
    else
        print_status "Service not yet enabled"
    fi
    
    # Validate service file
    if sudo systemctl status "$SERVICE_NAME" &>/dev/null; then
        print_status "Service file is valid"
    else
        print_status "Service file created (not yet started)"
    fi
}

# Create management script
create_management_script() {
    print_step "Creating service management script..."
    
    MANAGE_SCRIPT="$PROJECT_DIR/manage_service.sh"
    
    cat > "$MANAGE_SCRIPT" <<'EOF'
#!/bin/bash

# AI News Bot Service Management Script

SERVICE_NAME="ai-news-bot"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

show_usage() {
    echo "AI News Bot Service Manager"
    echo "Usage: $0 {start|stop|restart|status|enable|disable|logs|tail|update}"
    echo ""
    echo "Commands:"
    echo "  start     - Start the service"
    echo "  stop      - Stop the service"
    echo "  restart   - Restart the service"
    echo "  status    - Show service status"
    echo "  enable    - Enable service auto-start"
    echo "  disable   - Disable service auto-start"
    echo "  logs      - Show recent logs"
    echo "  tail      - Follow logs in real-time"
    echo "  update    - Update dependencies and restart"
}

start_service() {
    print_status "Starting $SERVICE_NAME service..."
    sudo systemctl start "$SERVICE_NAME"
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service started successfully"
    else
        print_error "Failed to start service"
        return 1
    fi
}

stop_service() {
    print_status "Stopping $SERVICE_NAME service..."
    sudo systemctl stop "$SERVICE_NAME"
    print_status "Service stopped"
}

restart_service() {
    print_status "Restarting $SERVICE_NAME service..."
    sudo systemctl restart "$SERVICE_NAME"
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service restarted successfully"
    else
        print_error "Failed to restart service"
        return 1
    fi
}

show_status() {
    echo "=== Service Status ==="
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
    echo ""
    echo "=== Service Info ==="
    echo "Enabled: $(sudo systemctl is-enabled "$SERVICE_NAME" 2>/dev/null || echo "disabled")"
    echo "Active: $(sudo systemctl is-active "$SERVICE_NAME" 2>/dev/null || echo "inactive")"
}

enable_service() {
    print_status "Enabling $SERVICE_NAME service for auto-start..."
    sudo systemctl enable "$SERVICE_NAME"
    print_status "Service enabled for auto-start"
}

disable_service() {
    print_status "Disabling $SERVICE_NAME service auto-start..."
    sudo systemctl disable "$SERVICE_NAME"
    print_status "Service auto-start disabled"
}

show_logs() {
    echo "=== Recent Logs ==="
    sudo journalctl -u "$SERVICE_NAME" --no-pager -l -n 50
}

tail_logs() {
    print_status "Following logs in real-time (Ctrl+C to exit)..."
    sudo journalctl -u "$SERVICE_NAME" -f
}

update_service() {
    print_status "Updating AI News Bot..."
    
    cd "$PROJECT_DIR"
    
    # Update dependencies
    poetry install --no-dev
    
    # Restart service
    restart_service
    
    print_status "Update completed"
}

case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    enable)
        enable_service
        ;;
    disable)
        disable_service
        ;;
    logs)
        show_logs
        ;;
    tail)
        tail_logs
        ;;
    update)
        update_service
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
EOF

    chmod +x "$MANAGE_SCRIPT"
    print_status "Management script created at: $MANAGE_SCRIPT"
}

# Create monitoring script
create_monitoring_script() {
    print_step "Creating monitoring script..."
    
    MONITOR_SCRIPT="$PROJECT_DIR/monitor_bot.sh"
    
    cat > "$MONITOR_SCRIPT" <<'EOF'
#!/bin/bash

# AI News Bot Monitoring Script

SERVICE_NAME="ai-news-bot"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== AI News Bot Monitor ==="
echo "Time: $(date)"
echo ""

# Service status
echo "🤖 Service Status:"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "  ✅ Service: RUNNING"
else
    echo "  ❌ Service: STOPPED"
fi

if systemctl is-enabled --quiet "$SERVICE_NAME"; then
    echo "  ✅ Auto-start: ENABLED"
else
    echo "  ⚠️  Auto-start: DISABLED"
fi

echo ""

# System resources
echo "💻 System Resources:"
echo "  Memory: $(free -h | awk '/^Mem:/ {printf "%.1f/%.1f GB (%.0f%%)", $3/1024/1024, $2/1024/1024, $3*100/$2}')"
echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')% usage"

# Temperature (if available)
if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    TEMP_C=$((TEMP/1000))
    echo "  Temperature: ${TEMP_C}°C"
fi

echo ""

# Recent activity
echo "📊 Recent Activity (last 24h):"
ERRORS=$(journalctl -u "$SERVICE_NAME" --since "24 hours ago" | grep -i error | wc -l)
ARTICLES=$(journalctl -u "$SERVICE_NAME" --since "24 hours ago" | grep "Successfully generated summary" | wc -l)
echo "  Articles processed: $ARTICLES"
echo "  Errors: $ERRORS"

echo ""

# Disk usage
echo "💾 Storage:"
echo "  Project size: $(du -sh "$PROJECT_DIR" | cut -f1)"
echo "  Logs size: $(du -sh "$PROJECT_DIR/logs" 2>/dev/null | cut -f1 || echo "0B")"
echo "  Models size: $(du -sh "$PROJECT_DIR/models" 2>/dev/null | cut -f1 || echo "0B")"

echo ""

# Last few log entries
echo "📝 Recent Logs:"
journalctl -u "$SERVICE_NAME" --no-pager -l -n 5 | sed 's/^/  /'

echo ""
echo "=== Monitor Complete ==="
EOF

    chmod +x "$MONITOR_SCRIPT"
    print_status "Monitoring script created at: $MONITOR_SCRIPT"
}

# Main setup function
main() {
    echo "🤖 AI News Aggregator Bot - Systemd Service Setup"
    echo "================================================="
    echo ""
    
    check_project_files
    check_poetry
    create_directories
    create_env_template
    install_dependencies
    create_service_file
    create_logrotate_config
    create_management_script
    create_monitoring_script
    test_service
    
    echo ""
    print_status "🎉 Systemd service setup completed!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Configure your .env file if not already done"
    echo "2. Enable and start the service:"
    echo "   sudo systemctl enable $SERVICE_NAME"
    echo "   sudo systemctl start $SERVICE_NAME"
    echo ""
    echo "🔧 Service Management:"
    echo "   ./manage_service.sh start     # Start the service"
    echo "   ./manage_service.sh stop      # Stop the service"
    echo "   ./manage_service.sh status    # Check status"
    echo "   ./manage_service.sh logs      # View logs"
    echo "   ./manage_service.sh tail      # Follow logs"
    echo ""
    echo "📊 Monitoring:"
    echo "   ./monitor_bot.sh              # Check system status"
    echo "   sudo journalctl -u $SERVICE_NAME -f  # Follow logs"
    echo ""
    echo "🚀 Auto-start on boot:"
    echo "   sudo systemctl enable $SERVICE_NAME"
    echo ""
    print_warning "Remember to configure your .env file before starting the service!"
}

# Run main function
main "$@"