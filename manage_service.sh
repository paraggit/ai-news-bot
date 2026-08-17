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
    
    # Update dependencies (check Poetry version)
    POETRY_VERSION=$(poetry --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    MAJOR_VERSION=$(echo "$POETRY_VERSION" | cut -d. -f1)
    MINOR_VERSION=$(echo "$POETRY_VERSION" | cut -d. -f2)
    
    if [[ $MAJOR_VERSION -gt 1 ]] || [[ $MAJOR_VERSION -eq 1 && $MINOR_VERSION -ge 2 ]]; then
        poetry install --only=main
    else
        poetry install --no-dev
    fi
    
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
