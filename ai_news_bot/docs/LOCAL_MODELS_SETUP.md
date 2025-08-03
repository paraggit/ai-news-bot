# 🤖 Local Models Setup Guide for Raspberry Pi

This comprehensive guide will help you set up and optimize local AI models on your Raspberry Pi for the AI News Aggregator Bot.

## 📋 Prerequisites

### Hardware Requirements

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Raspberry Pi** | Pi 4 - 2GB | Pi 4 - 4GB+ | Pi 5 supported |
| **Storage** | 16GB SD Card | 32GB+ SSD | SSD strongly recommended |
| **Cooling** | Passive heatsink | Active cooling | Prevents throttling |
| **Power** | Official 3A adapter | 3.5A+ adapter | Stable power crucial |

### Software Requirements

```bash
# Essential packages
sudo apt install -y python3-dev build-essential cmake
sudo apt install -y libopenblas-dev liblapack-dev
sudo apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev
```

## 🚀 Quick Setup

### 1. Automated Setup (Recommended)

```bash
# Run the optimization script
chmod +x setup_pi.sh
./setup_pi.sh

# Follow the prompts for automatic optimization
```

### 2. Manual Installation

```bash
# Install with local model support
poetry install --extras local-models

# For quantization support (memory-efficient)
poetry install --extras local-models-quantized

# Full installation with all optimizations
poetry install --extras local-models-full
```

## 🎯 Model Selection Strategy

### Step 1: Analyze Your System

```bash
# Get system recommendations
poetry run python -c "
from ai_news_bot.utils.model_optimizer import ModelOptimizer
optimizer = ModelOptimizer()
config = optimizer.get_optimal_config()
print(f'Your Pi: {config[\"system_info\"][\"architecture\"]} with {config[\"memory_info\"][\"total_ram_gb\"]:.1f}GB RAM')
print(f'Recommended tier: {config[\"tier\"]}')
print(f'Recommended model: {config[\"recommended_model\"]}')
print(f'Precision: {config[\"precision\"]}')
print(f'Quantization: {config[\"quantization\"]}')
"
```

### Step 2: Choose Configuration Based on Your Pi

#### **Pi 4 - 2GB RAM (Conservative)**
```bash
# .env configuration
SUMMARIZER_TYPE=local
LOCAL_MODEL_NAME=sshleifer/distilbart-cnn-6-6
LOCAL_MODEL_PRECISION=float16
LOCAL_MODEL_LOAD_IN_4BIT=true
LOCAL_MODEL_MAX_LENGTH=256
LOCAL_MODEL_BATCH_SIZE=1
```

#### **Pi 4 - 4GB RAM (Balanced)**
```bash
# .env configuration
SUMMARIZER_TYPE=local
LOCAL_MODEL_NAME=sshleifer/distilbart-cnn-12-6
LOCAL_MODEL_PRECISION=float16
LOCAL_MODEL_LOAD_IN_8BIT=true
LOCAL_MODEL_MAX_LENGTH=512
LOCAL_MODEL_BATCH_SIZE=1
```

#### **Pi 4 - 8GB RAM (Performance)**
```bash
# .env configuration
SUMMARIZER_TYPE=local
LOCAL_MODEL_NAME=facebook/bart-large-cnn
LOCAL_MODEL_PRECISION=float16
LOCAL_MODEL_MAX_LENGTH=1024
LOCAL_MODEL_BATCH_SIZE=1
```

#### **Pi 5 (Latest Hardware)**
```bash
# .env configuration
SUMMARIZER_TYPE=local
LOCAL_MODEL_NAME=facebook/bart-large-cnn
LOCAL_MODEL_PRECISION=float32
LOCAL_MODEL_MAX_LENGTH=1024
LOCAL_MODEL_BATCH_SIZE=1
```

## 🔧 Advanced Optimization

### Memory Optimization

#### Swap Configuration
```bash
# Check current swap
free -h

# Increase swap for model loading (if needed)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set: CONF_SWAPSIZE=2048

sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

#### Memory Monitoring
```bash
# Real-time memory monitoring
watch -n 1 'free -h && echo "---" && ps aux | grep python | head -3'

# Check model memory usage
poetry run python -c "
import psutil
from ai_news_bot.utils.model_optimizer import ModelOptimizer
optimizer = ModelOptimizer()
usage = optimizer.monitor_resource_usage()
for key, value in usage.items():
    if 'percent' in key:
        print(f'{key}: {value:.1f}%')
    else:
        print(f'{key}: {value}')
"
```

### CPU Optimization

```bash
# Set CPU governor to performance
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Check CPU frequency
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq

# Monitor CPU temperature
watch -n 1 'echo "CPU Temp: $(cat /sys/class/thermal/thermal_zone0/temp | awk "{print \$1/1000}")°C"'
```

### Storage Optimization

```bash
# Move model cache to faster storage (if using SSD)
mkdir -p /mnt/ssd/models
ln -s /mnt/ssd/models ~/.cache/huggingface

# Or configure in .env
LOCAL_MODEL_CACHE_DIR=/mnt/ssd/models
```

## 📊 Model Comparison & Benchmarking

### Performance Benchmarks

| Model | Size | Load Time | Inference Time | Memory Peak | Quality Score |
|-------|------|-----------|----------------|-------------|---------------|
| **distilbart-cnn-6-6** | 400MB | ~15s | ~3s | ~800MB | ⭐⭐⭐ |
| **distilbart-cnn-12-6** | 800MB | ~25s | ~5s | ~1.4GB | ⭐⭐⭐⭐ |
| **bart-large-cnn** | 1.6GB | ~45s | ~8s | ~2.8GB | ⭐⭐⭐⭐⭐ |
| **pegasus-xsum** | 600MB | ~20s | ~4s | ~1.1GB | ⭐⭐⭐⭐ |

*Benchmarks on Pi 4 - 4GB with SSD storage*

### Run Your Own Benchmark

```bash
# Create and run benchmark
cat > test_models.py << 'EOF'
import asyncio
import time
import psutil
import os
from ai_news_bot.config import load_config
from ai_news_bot.summarizer.local_summarizer import LocalSummarizer

async def benchmark_model(model_name, precision="float16", quantization=False):
    print(f"\n{'='*50}")
    print(f"Testing: {model_name}")
    print(f"Precision: {precision}, Quantization: {quantization}")
    print(f"{'='*50}")
    
    # Set environment variables
    os.environ["LOCAL_MODEL_NAME"] = model_name
    os.environ["LOCAL_MODEL_PRECISION"] = precision
    os.environ["LOCAL_MODEL_LOAD_IN_8BIT"] = str(quantization).lower()
    os.environ["SUMMARIZER_TYPE"] = "local"
    
    config = load_config()
    
    # Memory before
    memory_before = psutil.virtual_memory()
    print(f"Memory before: {memory_before.percent:.1f}%")
    
    try:
        # Load model
        start_time = time.time()
        summarizer = LocalSummarizer(config)
        load_time = time.time() - start_time
        
        # Memory after loading
        memory_after = psutil.virtual_memory()
        memory_used = memory_after.used - memory_before.used
        
        print(f"✅ Load time: {load_time:.1f}s")
        print(f"📊 Memory used: {memory_used / (1024**3):.2f}GB")
        print(f"📈 Memory total: {memory_after.percent:.1f}%")
        
        # Test summarization
        test_text = """
        OpenAI has announced a new breakthrough in artificial intelligence with the release of GPT-4 Turbo.
        The model features enhanced reasoning capabilities, improved factual accuracy, and a significantly
        larger context window of 128,000 tokens. This advancement enables more complex reasoning tasks
        and better understanding of lengthy documents. The model also demonstrates improved performance
        in mathematics, coding, and creative writing tasks compared to its predecessors.
        """
        
        start_time = time.time()
        summary = await summarizer.summarize("AI Breakthrough", test_text)
        inference_time = time.time() - start_time
        
        print(f"⚡ Inference time: {inference_time:.1f}s")
        print(f"📝 Summary length: {len(summary)} chars")
        print(f"📄 Summary preview: {summary[:100]}...")
        
        # Temperature check
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                print(f"🌡️  CPU Temperature: {temp:.1f}°C")
        except:
            print("🌡️  Temperature: Not available")
        
        await summarizer.close()
        return {
            "model": model_name,
            "load_time": load_time,
            "inference_time": inference_time,
            "memory_used_gb": memory_used / (1024**3),
            "summary_length": len(summary)
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

async def main():
    results = []
    
    # Test configurations
    test_configs = [
        ("sshleifer/distilbart-cnn-6-6", "float16", True),
        ("sshleifer/distilbart-cnn-12-6", "float16", True),
        ("facebook/bart-large-cnn", "float16", False),
    ]
    
    for model, precision, quantization in test_configs:
        result = await benchmark_model(model, precision, quantization)
        if result:
            results.append(result)
        
        # Cool down period
        await asyncio.sleep(5)
    
    # Summary
    print(f"\n{'='*50}")
    print("BENCHMARK SUMMARY")
    print(f"{'='*50}")
    
    for result in results:
        print(f"Model: {result['model']}")
        print(f"  Load: {result['load_time']:.1f}s | Inference: {result['inference_time']:.1f}s | Memory: {result['memory_used_gb']:.2f}GB")
        print()

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Run the benchmark
poetry run python test_models.py
```

## 🔍 Troubleshooting

### Common Issues

#### 1. **Model Loading Fails**
```bash
# Check available space
df -h

# Clear model cache
rm -rf ~/.cache/huggingface/transformers/

# Test with minimal model
LOCAL_MODEL_NAME=sshleifer/distilbart-cnn-6-6
LOCAL_MODEL_LOAD_IN_4BIT=true
```

#### 2. **Out of Memory Errors**
```bash
# Enable aggressive quantization
LOCAL_MODEL_LOAD_IN_4BIT=true
LOCAL_MODEL_MAX_LENGTH=256
LOCAL_MODEL_BATCH_SIZE=1

# Increase swap
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup && sudo dphys-swapfile swapon
```

#### 3. **Slow Performance**
```bash
# Check CPU throttling
vcgencmd measure_clock arm
vcgencmd measure_temp

# Ensure performance governor
sudo cpufreq-set -g performance

# Use SSD instead of SD card
# Move entire project to SSD mount point
```

#### 4. **High Temperature**
```bash
# Monitor temperature
watch -n 1 'vcgencmd measure_temp'

# If > 80°C, improve cooling:
# - Add heatsink
# - Use fan
# - Reduce overclock
# - Improve case ventilation
```

### Model-Specific Issues

#### **DistilBART Models**
- **Issue**: Poor quality summaries
- **Solution**: Use `pegasus-xsum` instead or increase max_length

#### **BART-Large**
- **Issue**: Too slow on Pi
- **Solution**: Enable 8-bit quantization or use distilbart

#### **T5 Models**
- **Issue**: Different input format
- **Solution**: Model handles this automatically, no changes needed

## 📈 Production Deployment

### Optimal Production Settings

For 24/7 operation on Raspberry Pi:

```bash
# .env for production
SUMMARIZER_TYPE=local
LOCAL_MODEL_NAME=sshleifer/distilbart-cnn-12-6
LOCAL_MODEL_PRECISION=float16
LOCAL_MODEL_LOAD_IN_8BIT=true
LOCAL_MODEL_MAX_LENGTH=512
LOCAL_MODEL_BATCH_SIZE=1
LOCAL_MODEL_CACHE_DIR=/mnt/ssd/models
ENABLE_PERFORMANCE_MONITORING=true
MEMORY_THRESHOLD_PERCENT=80
FETCH_INTERVAL_MINUTES=60
MAX_ARTICLES_PER_RUN=5
```

### Health Monitoring

```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash

echo "=== AI News Bot Health Check ==="
echo "Time: $(date)"

# Check if service is running
if systemctl is-active --quiet ai-news-bot; then
    echo "✅ Service: RUNNING"
else
    echo "❌ Service: STOPPED"
fi

# Check memory usage
MEMORY=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
echo "📊 Memory Usage: ${MEMORY}%"

# Check temperature
if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    TEMP_C=$((TEMP/1000))
    echo "🌡️  Temperature: ${TEMP_C}°C"
fi

# Check disk space
DISK=$(df / | awk 'NR==2 {printf("%.1f", $5)}' | sed 's/%//')
echo "💾 Disk Usage: ${DISK}%"

# Check recent logs for errors
ERROR_COUNT=$(journalctl -u ai-news-bot --since "1 hour ago" | grep -i error | wc -l)
echo "🐛 Recent Errors: ${ERROR_COUNT}"

echo "=========================="
EOF

chmod +x health_check.sh

# Add to crontab for regular checks
echo "*/30 * * * * /path/to/health_check.sh >> /var/log/ai-news-health.log" | crontab -
```

### Performance Tuning

```bash
# Optimize for long-running operation
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# Ensure consistent performance
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Add to rc.local for persistence
echo 'echo performance > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor' | sudo tee -a /etc/rc.local
```

## 🎯 Next Steps

1. **Start with recommended configuration** based on your Pi model
2. **Run benchmarks** to validate performance
3. **Monitor resource usage** during initial runs
4. **Adjust configuration** based on observed performance
5. **Set up health monitoring** for production deployment

For additional help, check the main README.md troubleshooting section or create an issue in the project repository.