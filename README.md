![GxhVae5XsAcI4zJ](https://github.com/user-attachments/assets/1cf8d0f1-c3d1-493d-835e-9e78cd0200e7)

**[TELEGRAM Link: AI_NEWS_HUB_3310](https://t.me/ai_news_hub_3310)**

## 🎯 NEW: Perplexity Search API Integration (Nov 2025)

The bot now uses **Perplexity AI's Search API** to actively search the web for the latest AI research! 🔍

**Why This is Game-Changing:**
- 🌐 **Searches Entire Web**: Finds research from ANY source, not just RSS feeds
- 🎯 **Customizable Queries**: Search for exactly what you want to track
- 🔄 **Real-time Discovery**: Gets the most recent content (last 30 days)
- 🤖 **AI-Powered**: Perplexity's AI curates and summarizes findings
- 📊 **Comprehensive Coverage**: Discovers content you'd never find otherwise

**Quick Start:**
```bash
# 1. Get API key from https://www.perplexity.ai/
# 2. Add to .env:
echo "PERPLEXITY_API_KEY=pplx-your-key-here" >> .env

# 3. Run the bot (Perplexity auto-enabled)
poetry run python -m ai_news_bot.main
```

**Documentation:**
- 📖 **[Setup Guide](PERPLEXITY_SEARCH_SETUP.md)** - Complete integration guide
- 📖 **[Example Config](PERPLEXITY_ENV_EXAMPLE.txt)** - Quick configuration example

## 🎯 Agentic AI & AI Tools Coverage (Nov 2025)

The bot now **comprehensively tracks Agentic AI, AI agents, AI tools, and frameworks** including LangChain, LangGraph, Model Context Protocol (MCP), and more!

**What's Covered:**
- ✅ 24 RSS feeds covering LangChain, Anthropic, Hugging Face, LlamaIndex, Perplexity, etc.
- ✅ 5 new topic categories: Agentic AI, AI Frameworks, MCP, AI Bots, MLOps
- ✅ 280+ keywords for better detection (up from ~100)
- ✅ Prioritizes agent systems, tool use, and framework updates
- ✅ Research papers on multi-agent systems and agent architectures

## 🎯 Research-Focused Filtering (Nov 2025)

The bot **focuses on research breakthroughs and technical innovations** while **filtering out investment news** and funding announcements! 

**Features:**
- ✅ Prioritizes research breakthroughs, discoveries, and novel inventions
- ❌ Filters out funding rounds, acquisitions, and business deals
- 🔥 Special indicators for breakthrough articles
- 🎓 Focus on academic and research sources (ArXiv, Nature, IEEE, university labs)
- ⭐ Quality scores shown for high-relevance articles

## 🔧 Raspberry Pi Optimization

### **Automated Setup Script**

Run the automated setup script for optimal Raspberry Pi configuration:

```bash
# Make setup script executable
chmod +x setup_pi.sh

# Run the optimization script
./setup_pi.sh
```

The script will:
- ✅ Update system packages and install dependencies
- ✅ Optimize memory settings and create swap file
- ✅ Set CPU governor to performance mode
- ✅ Install ARM64-optimized PyTorch
- ✅ Create systemd service for auto-start
- ✅ Set up monitoring tools
- ✅ Analyze your system and recommend optimal model configuration

### **Manual Performance Tuning**

1. **Memory Management**:
   ```bash
   # Increase swap if using local models
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

2. **CPU Governor**:
   ```bash
   # Set performance mode
   echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

3. **Local Model Optimization**:
   ```bash
   # For maximum memory efficiency
   poetry install --extras local-models-quantized
   
   # Check system recommendations
   poetry run python -c "
   from ai_news_bot.utils.model_optimizer import ModelOptimizer
   optimizer = ModelOptimizer()
   config = optimizer.get_optimal_config()
   print(f'Recommended: {config[\"recommended_model\"]}')
   for tip in optimizer.get_performance_recommendations()[:5]:
       print(f'• {tip}')
   "
   ```

### **Model Selection Guide**

Use the built-in system analyzer to get personalized recommendations:

```bash
# Analyze your system and get recommendations
poetry run python -m ai_news_bot.utils.model_optimizer

# This will output:
# - Your system specifications
# - Recommended model tier
# - Optimal configuration settings
# - Performance tips specific to your hardware
```

### **Memory Monitoring**

Monitor resource usage during operation:

```bash
# Real-time monitoring
./monitor_pi.sh

# Or check individual components
poetry run python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent:.1f}%')
print(f'CPU: {psutil.cpu_percent():.1f}%')
if hasattr(psutil, 'sensors_temperatures'):
    temps = psutil.sensors_temperatures()
    if temps: print(f'Temp: {list(temps.values())[0][0].current}°C')
"
```

### **Local Model Performance Comparison**

| Model | Size | RAM Usage | Speed | Quality | Pi 4 Compatible |
|-------|------|-----------|-------|---------|------------------|
| `distilbart-cnn-6-6` | 400MB | ~600MB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ All variants |
| `distilbart-cnn-12-6` | 800MB | ~1.2GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ 2GB+ models |
| `bart-large-cnn` | 1.6GB | ~2.5GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ 4GB+ models |
| `pegasus-xsum` | 600MB | ~900MB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ 2GB+ models |
| `t5-small` | 300MB | ~500MB | ⭐⭐⭐⭐⭐ | ⭐⭐ | ✅ All variants |

### **Quantization Benefits**

| Technique | Memory Reduction | Quality Loss | Setup |
|-----------|------------------|--------------|-------|
| FP16 | ~50% | Minimal | `LOCAL_MODEL_PRECISION=float16` |
| 8-bit | ~75% | Small | `LOCAL_MODEL_LOAD_IN_8BIT=true` |
| 4-bit | ~87% | Moderate | `LOCAL_MODEL_LOAD_IN_4BIT=true` |

### **Systemd Service Setup**

The setup script creates a systemd service automatically, but you can also set it up manually:

```bash
sudo nano /etc/systemd/system/ai-news-bot.service
```

```ini
[Unit]
Description=AI News Aggregator Bot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ai-news-aggregator
Environment=PATH=/home/pi/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/pi/.local/bin/poetry run ai-news-bot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ai-news-bot
sudo systemctl start ai-news-bot

# Check status
sudo systemctl status ai-news-bot

# View logs
sudo journalctl -u ai-news-bot -f
```# 🤖 AI News Aggregator Bot

A comprehensive **AI-powered news aggregation system** designed specifically for **Raspberry Pi** that monitors the latest AI developments, summarizes content using LLMs, and automatically posts updates to Telegram channels.

## 🌟 Features

### 📰 **Multi-Source News Monitoring**
- **RSS Feeds**: TechCrunch AI, VentureBeat AI, MIT Technology Review, Wired, The Verge
- **Official Blogs**: OpenAI, Google AI, DeepMind blog posts via web scraping
- **Research Papers**: Latest AI research from arXiv.org (cs.AI, cs.LG, cs.CL, cs.CV)

### 🧠 **Smart Summarization**
- **OpenAI GPT**: High-quality summaries using GPT-3.5-turbo or GPT-4
- **DeepSeek API**: Cost-effective alternative with competitive quality
- **Local Models**: Offline summarization using HuggingFace transformers

### 📱 **Telegram Integration**
- Automated posting to channels/groups
- Rich message formatting with emojis and hashtags
- Intelligent message splitting for long content
- Rate limiting and error handling

### 🔍 **Advanced Search & Discovery** ⭐ NEW!
- **Full-Text Search**: Fast SQLite FTS5 search across all articles
- **AI Relevance Scoring**: Automatic scoring (0-100) of article relevance
- **Topic Categorization**: 10 AI topic categories (LLMs, CV, NLP, etc.)
- **Smart Deduplication**: Intelligent detection of similar articles
- **Trending Analysis**: Identify hot topics in AI research
- **CLI Search Tool**: Search your database from the command line
- **Advanced Filtering**: Filter by source, topic, relevance, date range

### 🔧 **Production Features**
- **Async Architecture**: Non-blocking I/O for efficient resource usage
- **SQLite Database**: Track processed articles and prevent duplicates
- **Scheduled Jobs**: Configurable intervals for news fetching
- **Robust Error Handling**: Comprehensive logging and recovery
- **ARM64 Optimized**: Specifically designed for Raspberry Pi performance

## 🏗️ Project Structure

```
ai-news-aggregator/
├── pyproject.toml              # Poetry configuration and dependencies
├── README.md                   # This file
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── ai_news_bot/               # Main application package
│   ├── __init__.py
│   ├── main.py                # Application entry point
│   ├── config.py              # Configuration management
│   ├── database.py            # SQLite database operations
│   ├── news_sources/          # News source implementations
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract base classes
│   │   ├── rss_feeds.py       # RSS feed processor
│   │   ├── arxiv.py           # ArXiv research papers
│   │   └── web_scraper.py     # Web scraping for blogs
│   ├── summarizer/            # Content summarization
│   │   ├── __init__.py
│   │   ├── base.py            # Summarizer base class
│   │   ├── openai_summarizer.py
│   │   ├── deepseek_summarizer.py
│   │   └── local_summarizer.py
│   ├── telegram/              # Telegram bot integration
│   │   ├── __init__.py
│   │   └── bot.py
│   └── utils/                 # Utility modules
│       ├── __init__.py
│       ├── logger.py          # Logging configuration
│       └── helpers.py         # Helper functions
├── data/                      # Database and data files
│   └── news_aggregator.db     # SQLite database
└── logs/                      # Application logs
    └── app.log
```

## 🔍 Search Features Quick Start

The news aggregator now includes powerful search and discovery features! 

### **Search from Command Line**

```bash
# Search for articles about GPT
python -m ai_news_bot.cli_search search --query "GPT"

# Filter by AI topic
python -m ai_news_bot.cli_search search --topic "Large Language Models"

# Get top articles from last 24 hours  
python -m ai_news_bot.cli_search top

# Show trending topics
python -m ai_news_bot.cli_search trending

# Database statistics
python -m ai_news_bot.cli_search stats

# See all available topics
python -m ai_news_bot.cli_search topics
```

### **Search from Python**

```python
from ai_news_bot.database import DatabaseManager
from ai_news_bot.utils import NewsSearchEngine

db = DatabaseManager("data/news_aggregator.db")
await db.initialize()
search_engine = NewsSearchEngine(db)

# Search with filters
results = await search_engine.search(
    query="transformer",
    topics=["Large Language Models"],
    min_relevance=70.0,
    days_back=7
)
```

📚 **For detailed documentation, see:**
- `SEARCH_IMPROVEMENTS_SUMMARY.md` - Quick overview
- `NEWS_SEARCH_IMPROVEMENTS.md` - Complete documentation
- `examples/search_examples.py` - Example scripts

---

## 🚀 Quick Start

### 1. **Prerequisites**

Ensure your Raspberry Pi has Python 3.9+ and Poetry installed:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+ (if not already installed)
sudo apt install python3 python3-pip python3-dev -y

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 2. **Clone and Setup Project**

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-news-aggregator

# Install dependencies
poetry install

# For local model support (optional, requires more resources)
poetry install --extras local-models
```

### 3. **Configure Environment**

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Configuration:**
```bash
# Telegram Bot (Required)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHANNEL_ID=@your_channel_or_chat_id

# Choose ONE summarizer
SUMMARIZER_TYPE=openai  # or 'deepseek' or 'local'

# If using OpenAI
OPENAI_API_KEY=your_openai_api_key

# If using DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key

# Fetch interval (minutes)
FETCH_INTERVAL_MINUTES=30
```

### 4. **Setup Telegram Bot**

1. **Create Bot**: Message [@BotFather](https://t.me/botfather) on Telegram
   ```
   /newbot
   ```
   
2. **Get Token**: Save the bot token to your `.env` file

3. **Create Channel**: Create a new Telegram channel for AI news

4. **Add Bot**: Add your bot as an administrator to the channel

5. **Get Channel ID**: 
   ```bash
   # Test your setup
   poetry run python -c "
   import asyncio
   from ai_news_bot.telegram.bot import TelegramBot
   from ai_news_bot.config import load_config
   
   async def test():
       config = load_config()
       bot = TelegramBot(config.telegram_bot_token)
       await bot.send_test_message(config.telegram_channel_id)
   
   asyncio.run(test())
   "
   ```

### 5. **Fix SSL Issues (macOS/Linux)**

If you encounter SSL certificate errors:

```bash
# Quick automated fix
poetry run python fix_ssl.py

# Test connectivity
poetry run python test_connectivity.py

# Manual macOS fix
/Applications/Python\ 3.x/Install\ Certificates.command
```

### 6. **Run the Bot**

```bash
# Start the bot
poetry run ai-news-bot

# Or run directly
poetry run python -m ai_news_bot.main
```

## ⚙️ Configuration Options

### **Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | - | ✅ |
| `TELEGRAM_CHANNEL_ID` | Channel/chat ID | - | ✅ |
| `SUMMARIZER_TYPE` | Summarizer type | `openai` | ✅ |
| `OPENAI_API_KEY` | OpenAI API key | - | If using OpenAI |
| `DEEPSEEK_API_KEY` | DeepSeek API key | - | If using DeepSeek |
| `FETCH_INTERVAL_MINUTES` | News fetch interval | `30` | ❌ |
| `MAX_ARTICLES_PER_RUN` | Max articles per cycle | `10` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `ARXIV_MAX_RESULTS` | ArXiv papers per fetch | `5` | ❌ |

### **Local Model Configuration**

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `LOCAL_MODEL_NAME` | HuggingFace model | `facebook/bart-large-cnn` | See recommendations below |
| `LOCAL_MODEL_DEVICE` | Device for inference | `auto` | `auto`, `cpu`, `cuda` |
| `LOCAL_MODEL_PRECISION` | Model precision | `float16` | `float32`, `float16` |
| `LOCAL_MODEL_MAX_LENGTH` | Max input length | `1024` | `256-2048` |
| `LOCAL_MODEL_BATCH_SIZE` | Batch size | `1` | `1-4` (Pi: use 1) |
| `LOCAL_MODEL_CACHE_DIR` | Model cache directory | `./models` | Any valid path |
| `LOCAL_MODEL_USE_QUANTIZATION` | Enable quantization | `false` | `true`, `false` |
| `LOCAL_MODEL_LOAD_IN_8BIT` | 8-bit quantization | `false` | `true`, `false` |
| `LOCAL_MODEL_LOAD_IN_4BIT` | 4-bit quantization | `false` | `true`, `false` |

### **Recommended Models for Raspberry Pi**

#### **Ultra-Light (< 1GB RAM available)**
```bash
LOCAL_MODEL_NAME=sshleifer/distilbart-cnn-6-6     # 400MB, fastest
LOCAL_MODEL_LOAD_IN_4BIT=true
LOCAL_MODEL_MAX_LENGTH=256
```

#### **Light (1-2GB RAM available)**
```bash
LOCAL_MODEL_NAME=sshleifer/distilbart-cnn-12-6    # 800MB, good quality
LOCAL_MODEL_LOAD_IN_8BIT=true
LOCAL_MODEL_MAX_LENGTH=512
```

#### **Standard (2-4GB RAM available)**
```bash
LOCAL_MODEL_NAME=facebook/bart-large-cnn          # 1.6GB, high quality
LOCAL_MODEL_PRECISION=float16
LOCAL_MODEL_MAX_LENGTH=1024
```

#### **Alternative Models**
- `google/pegasus-xsum` - 600MB, good for news summarization
- `google/pegasus-cnn_dailymail` - 2.2GB, excellent quality
- `t5-small` - 300MB, very fast but basic quality

### **News Sources Configuration**

The bot monitors these sources by default:

**RSS Feeds:**
- TechCrunch AI
- VentureBeat AI  
- MIT Technology Review AI
- Wired AI
- The Verge AI

**Web Scraping:**
- OpenAI Blog
- Google AI Blog
- DeepMind Blog

**Research Papers:**
- arXiv categories: cs.AI, cs.LG, cs.CL, cs.CV

## 🔧 Raspberry Pi Optimization

### **Performance Tuning**

1. **Memory Management**:
   ```bash
   # Increase swap if using local models
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

2. **CPU Governor**:
   ```bash
   # Set performance mode
   echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

3. **Local Models** (if using):
   ```bash
   # Install optimized PyTorch for ARM
   poetry install --extras local-models
   
   # For better performance, consider using lighter models:
   # facebook/bart-large-cnn (default)
   # google/pegasus-xsum (smaller)
   # sshleifer/distilbart-cnn-12-6 (fastest)
   ```

### **Systemd Service Setup**

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/ai-news-bot.service
```

```ini
[Unit]
Description=AI News Aggregator Bot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ai-news-aggregator
Environment=PATH=/home/pi/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/home/pi/.local/bin/poetry run ai-news-bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ai-news-bot
sudo systemctl start ai-news-bot

# Check status
sudo systemctl status ai-news-bot
```

## 🛠️ Development

### **Project Commands**

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Code formatting
poetry run black ai_news_bot/

# Type checking
poetry run mypy ai_news_bot/

# Linting
poetry run flake8 ai_news_bot/
```

### **Database Management**

```bash
# View database statistics
poetry run python -c "
import asyncio
from ai_news_bot.database import DatabaseManager
from ai_news_bot.config import load_config

async def stats():
    config = load_config()
    db = DatabaseManager(config.database_path)
    await db.initialize()
    stats = await db.get_statistics()
    print(stats)
    await db.close()

asyncio.run(stats())
"

# Clean old data (30+ days)
poetry run python -c "
import asyncio
from ai_news_bot.database import DatabaseManager
from ai_news_bot.config import load_config

async def cleanup():
    config = load_config()
    db = DatabaseManager(config.database_path)
    await db.initialize()
    await db.cleanup_old_data(days=30)
    await db.close()

asyncio.run(cleanup())
"
```

## 📊 Monitoring & Logs

### **Log Locations**
- **Application Logs**: `logs/app.log`
- **Systemd Logs**: `sudo journalctl -u ai-news-bot -f`

### **Log Levels**
- `DEBUG`: Detailed debugging information
- `INFO`: General operational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

### **Health Monitoring**

```bash
# Check if bot is running
ps aux | grep ai-news-bot

# Monitor resource usage
htop

# Check database size
du -h data/news_aggregator.db

# Monitor network usage
iftop
```

## 🚨 Troubleshooting

### **Common Issues**

1. **SSL Certificate Errors (macOS)**:
   ```bash
   # Quick fix script
   poetry run python fix_ssl.py
   
   # Manual fix for macOS
   /Applications/Python\ 3.x/Install\ Certificates.command
   
   # Or update certifi
   poetry run pip install --upgrade certifi
   
   # Test connectivity
   poetry run python test_connectivity.py
   
   # Temporary bypass (testing only!)
   echo "SSL_VERIFY=false" >> .env
   ```

2. **Bot Not Posting to Channel**:
   - Verify bot token is correct
   - Ensure bot is admin in channel
   - Check channel ID format (`@channelname` or `-1001234567890`)

3. **Memory Issues on Raspberry Pi**:
   - Switch to `openai` or `deepseek` summarizer
   - Use lighter local model: `sshleifer/distilbart-cnn-6-6`
   - Enable quantization: `LOCAL_MODEL_LOAD_IN_4BIT=true`
   - Increase swap space
   - Reduce `MAX_ARTICLES_PER_RUN`

4. **Local Model Not Loading**:
   ```bash
   # Check system recommendations
   poetry run python -c "
   from ai_news_bot.utils.model_optimizer import ModelOptimizer
   optimizer = ModelOptimizer()
   validation = optimizer.validate_model_requirements('facebook/bart-large-cnn')
   print('Can run:', validation['can_run'])
   for warning in validation['warnings']: print(f'⚠️  {warning}')
   for rec in validation['recommendations']: print(f'💡 {rec}')
   "
   
   # Try alternative model
   LOCAL_MODEL_NAME=sshleifer/distilbart-cnn-6-6
   LOCAL_MODEL_LOAD_IN_4BIT=true
   ```

5. **Network Connectivity Issues**:
   ```bash
   # Test network connectivity
   poetry run python test_connectivity.py
   
   # Check if behind corporate firewall
   ping google.com
   
   # Test Telegram API
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

6. **Slow Performance**:
   - Use CPU performance governor: `sudo cpufreq-set -g performance`
   - Ensure adequate cooling (check temperature)
   - Use faster storage (SSD over SD card)
   - Enable model quantization
   - Reduce batch size to 1

7. **High Memory Usage**:
   ```bash
   # Monitor memory usage
   watch -n 1 'free -h && echo "---" && ps aux | grep python | head -5'
   
   # Clean up model cache
   rm -rf ~/.cache/huggingface/transformers/
   
   # Use memory-efficient settings
   LOCAL_MODEL_PRECISION=float16
   LOCAL_MODEL_LOAD_IN_8BIT=true
   LOCAL_MODEL_MAX_LENGTH=512
   ```

3. **Rate Limiting**:
   - Increase `FETCH_INTERVAL_MINUTES`
   - Check API quotas
   - Monitor Telegram rate limits

4. **Network Connectivity**:
   ```bash
   # Test internet connection
   ping google.com
   
   # Test Telegram API
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

### **Debug Mode**

```bash
# Run with debug logging
LOG_LEVEL=DEBUG poetry run ai-news-bot

# Test individual components
poetry run python -c "
import asyncio
from ai_news_bot.news_sources.rss_feeds import RSSFeedSource
from ai_news_bot.config import load_config

async def test_rss():
    config = load_config()
    source = RSSFeedSource(config)
    await source.initialize()
    articles = await source.fetch_articles()
    print(f'Found {len(articles)} articles')
    await source.close()

asyncio.run(test_rss())
"

# Test local model setup
poetry run python -c "
from ai_news_bot.utils.model_optimizer import ModelOptimizer
optimizer = ModelOptimizer()
print('System Analysis:')
print(f'Architecture: {optimizer.system_info[\"architecture\"]}')
print(f'Available RAM: {optimizer.memory_info[\"available_ram_gb\"]:.1f}GB')
config = optimizer.get_optimal_config()
print(f'Recommended model: {config[\"recommended_model\"]}')
"

# Test summarizer
poetry run python -c "
import asyncio
from ai_news_bot.summarizer.local_summarizer import LocalSummarizer
from ai_news_bot.config import load_config

async def test_summarizer():
    config = load_config()
    if config.summarizer_type == 'local':
        summarizer = LocalSummarizer(config)
        summary = await summarizer.summarize(
            'Test Article', 
            'This is a test article about artificial intelligence developments.'
        )
        print(f'Summary: {summary}')
    else:
        print('Local summarizer not configured')

asyncio.run(test_summarizer())
"
```

### **Performance Benchmarking**

Test different model configurations:

```bash
# Create benchmark script
cat > benchmark_models.py << 'EOF'
import asyncio
import time
import psutil
from ai_news_bot.config import load_config
from ai_news_bot.summarizer.local_summarizer import LocalSummarizer

async def benchmark_model(model_name):
    print(f"\nTesting model: {model_name}")
    
    # Create temporary config
    config = load_config()
    config.local_model_name = model_name
    config.summarizer_type = "local"
    
    try:
        # Initialize summarizer
        start_time = time.time()
        summarizer = LocalSummarizer(config)
        init_time = time.time() - start_time
        
        # Test summarization
        test_content = "Artificial intelligence continues to advance rapidly. New developments in machine learning are transforming various industries. Researchers are making breakthroughs in natural language processing and computer vision."
        
        start_time = time.time()
        summary = await summarizer.summarize("AI Test", test_content)
        summarize_time = time.time() - start_time
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        print(f"✅ Model loaded in {init_time:.1f}s")
        print(f"✅ Summarization took {summarize_time:.1f}s") 
        print(f"📊 Memory usage: {memory.percent:.1f}%")
        print(f"📝 Summary length: {len(summary)} chars")
        
        await summarizer.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    models = [
        "sshleifer/distilbart-cnn-6-6",
        "sshleifer/distilbart-cnn-12-6", 
        "facebook/bart-large-cnn"
    ]
    
    for model in models:
        await benchmark_model(model)
        await asyncio.sleep(2)  # Cool down

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Run benchmark
poetry run python benchmark_models.py
```

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/ai-news-aggregator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/ai-news-aggregator/discussions)
- **Documentation**: This README and inline code comments

---

**Made with ❤️ for the AI community** 🚀
