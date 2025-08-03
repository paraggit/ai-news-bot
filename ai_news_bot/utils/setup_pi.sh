#!/bin/bash

# AI News Aggregator Bot - Raspberry Pi Setup Script
# This script optimizes your Raspberry Pi for running local AI models

set -e

echo "🤖 AI News Aggregator Bot - Raspberry Pi Setup"
echo "=============================================="
echo ""

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

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "This script is optimized for Raspberry Pi but can work on other ARM systems"
    else
        print_status "Raspberry Pi detected"
    fi
}

# Get system information
get_system_info() {
    print_step "Checking system information..."
    
    # Memory info
    TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
    AVAILABLE_MEM=$(free -h | awk '/^Mem:/ {print $7}')
    
    # CPU info
    CPU_CORES=$(nproc)
    CPU_ARCH=$(uname -m)
    
    print_status "Total Memory: $TOTAL_MEM"
    print_status "Available Memory: $AVAILABLE_MEM"
    print_status "CPU Cores: $CPU_CORES"
    print_status "Architecture: $CPU_ARCH"
    
    # Temperature check (Pi specific)
    if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
        TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
        TEMP_C=$((TEMP/1000))
        print_status "CPU Temperature: ${TEMP_C}°C"
        
        if [ $TEMP_C -gt 70 ]; then
            print_warning "High CPU temperature detected. Consider improving cooling."
        fi
    fi
}

# Update system packages
update_system() {
    print_step "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    
    # Install essential packages
    print_step "Installing essential packages..."
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-dev \
        python3-venv \
        build-essential \
        git \
        curl \
        wget \
        htop \
        iotop \
        cmake \
        libopenblas-dev \
        liblapack-dev \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libwebp-dev \
        tcl8.6-dev \
        tk8.6-dev \
        python3-tk
}

# Install Poetry
install_poetry() {
    print_step "Installing Poetry..."
    
    if command -v poetry &> /dev/null; then
        print_status "Poetry already installed"
        poetry --version
    else
        curl -sSL https://install.python-poetry.org | python3 -
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin:$PATH"
        print_status "Poetry installed successfully"
    fi
}

# Optimize memory settings
optimize_memory() {
    print_step "Optimizing memory settings..."
    
    # Increase swap size for model loading
    CURRENT_SWAP=$(free -h | awk '/^Swap:/ {print $2}')
    print_status "Current swap: $CURRENT_SWAP"
    
    if [ "$CURRENT_SWAP" = "0B" ] || [ -z "$CURRENT_SWAP" ]; then
        print_step "Setting up swap file..."
        
        # Create 2GB swap file
        sudo fallocate -l 2G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        
        # Make permanent
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        
        print_status "2GB swap file created"
    else
        print_status "Swap already configured"
    fi
    
    # Optimize swap usage
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
}

# Install PyTorch for ARM64
install_pytorch_arm() {
    print_step "Installing PyTorch for ARM64..."
    
    # Install PyTorch with ARM64 optimizations
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    
    print_status "PyTorch installed for ARM64"
}

# Set CPU governor to performance
optimize_cpu() {
    print_step "Optimizing CPU settings..."
    
    # Set CPU governor to performance
    if [ -f "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor" ]; then
        echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
        print_status "CPU governor set to performance mode"
    else
        print_warning "CPU frequency scaling not available"
    fi
    
    # Increase GPU memory split for better performance
    if command -v raspi-config &> /dev/null; then
        print_step "Optimizing GPU memory split..."
        sudo raspi-config nonint do_memory_split 16
        print_status "GPU memory split optimized"
    fi
}

# Create model directory and set permissions
setup_model_directory() {
    print_step "Setting up model directory..."
    
    mkdir -p models
    mkdir -p data
    mkdir -p logs
    
    # Set proper permissions
    chmod 755 models data logs
    
    print_status "Directories created: models/, data/, logs/"
}

# Analyze system and create optimal configuration
create_optimal_config() {
    print_step "Analyzing system for optimal configuration..."
    
    # Run the model optimizer
    if [ -f "ai_news_bot/utils/model_optimizer.py" ]; then
        python3 -c "
from ai_news_bot.utils.model_optimizer import ModelOptimizer, create_model_config_file
optimizer = ModelOptimizer()
config = optimizer.get_optimal_config()
print(f'Recommended model: {config[\"recommended_model\"]}')
print(f'Recommended tier: {config[\"tier\"]}')
create_model_config_file()
"
        print_status "Optimal configuration saved to model_config.json"
    else
        print_warning "Model optimizer not found. Run after installing the project."
    fi
}

# Create systemd service
create_service() {
    print_step "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/ai-news-bot.service"
    WORKING_DIR=$(pwd)
    USER=$(whoami)
    
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=AI News Aggregator Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORKING_DIR
Environment=PATH=/home/$USER/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/$USER/.local/bin/poetry run ai-news-bot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    print_status "Systemd service created at $SERVICE_FILE"
    print_status "Enable with: sudo systemctl enable ai-news-bot"
    print_status "Start with: sudo systemctl start ai-news-bot"
}

# Performance monitoring setup
setup_monitoring() {
    print_step "Setting up performance monitoring..."
    
    # Install system monitoring tools
    sudo apt install -y htop iotop nethogs
    
    # Create monitoring script
    cat > monitor_pi.sh << 'EOF'
#!/bin/bash

# Simple monitoring script for Raspberry Pi
echo "=== Raspberry Pi System Monitor ==="
echo "Date: $(date)"
echo ""

# Temperature
if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    TEMP_C=$((TEMP/1000))
    echo "CPU Temperature: ${TEMP_C}°C"
fi

# Memory usage
echo ""
echo "Memory Usage:"
free -h

# CPU usage
echo ""
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "CPU Usage: " 100 - $1 "%"}'

# Disk usage
echo ""
echo "Disk Usage:"
df -h | grep -E '^/dev/'

# Check if AI bot is running
echo ""
if pgrep -f "ai-news-bot" > /dev/null; then
    echo "AI News Bot: RUNNING ✓"
else
    echo "AI News Bot: NOT RUNNING ✗"
fi

# Model memory usage (if process exists)
if pgrep -f "python.*ai_news_bot" > /dev/null; then
    echo ""
    echo "Bot Memory Usage:"
    ps aux | grep -E "python.*ai_news_bot" | head -1 | awk '{print "RSS: " $6/1024 " MB, VSZ: " $5/1024 " MB"}'
fi
EOF

    chmod +x monitor_pi.sh
    print_status "Monitoring script created: ./monitor_pi.sh"
}

# Main installation flow
main() {
    echo "Starting Raspberry Pi optimization for AI News Aggregator Bot..."
    echo ""
    
    check_raspberry_pi
    get_system_info
    echo ""
    
    # Ask for confirmation
    read -p "Do you want to proceed with the optimization? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Setup cancelled."
        exit 0
    fi
    
    update_system
    install_poetry
    optimize_memory
    optimize_cpu
    install_pytorch_arm
    setup_model_directory
    create_optimal_config
    create_service
    setup_monitoring
    
    echo ""
    print_status "🎉 Raspberry Pi optimization complete!"
    echo ""
    echo "Next steps:"
    echo "1. Install the project: poetry install"
    echo "2. Configure your .env file"
    echo "3. Run the bot: poetry run ai-news-bot"
    echo "4. Monitor system: ./monitor_pi.sh"
    echo ""
    echo "Optional for local models:"
    echo "- poetry install --extras local-models"
    echo "- Check model_config.json for recommendations"
    echo ""
    print_warning "Reboot recommended to apply all optimizations: sudo reboot"
}

# Run main function
main "$@"