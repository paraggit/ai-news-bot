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
