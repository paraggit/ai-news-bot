#!/usr/bin/env python3
"""
Test script to verify AI News Aggregator installation.

This script checks if all components are properly installed and configured.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from ai_news_bot.config import load_config
        print("✅ Config module imported successfully")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from ai_news_bot.utils.logger import setup_logger
        print("✅ Logger module imported successfully")
    except ImportError as e:
        print(f"❌ Logger import failed: {e}")
        return False
    
    try:
        from ai_news_bot.database import DatabaseManager
        print("✅ Database module imported successfully")
    except ImportError as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    try:
        from ai_news_bot.telegram.bot import TelegramBot
        print("✅ Telegram bot module imported successfully")
    except ImportError as e:
        print(f"❌ Telegram bot import failed: {e}")
        return False
    
    try:
        from ai_news_bot.news_sources import get_all_news_sources
        print("✅ News sources module imported successfully")
    except ImportError as e:
        print(f"❌ News sources import failed: {e}")
        return False
    
    try:
        from ai_news_bot.summarizer import get_summarizer
        print("✅ Summarizer module imported successfully")
    except ImportError as e:
        print(f"❌ Summarizer import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading."""
    print("\n📝 Testing configuration...")
    
    try:
        from ai_news_bot.config import load_config
        
        # Create a test .env file if it doesn't exist
        if not Path(".env").exists():
            print("ℹ️  No .env file found, testing with defaults")
            
            # Set minimal environment variables for testing
            os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
            os.environ["TELEGRAM_CHANNEL_ID"] = "@test_channel"
            os.environ["SUMMARIZER_TYPE"] = "openai"
            os.environ["OPENAI_API_KEY"] = "test_key"
        
        config = load_config()
        print("✅ Configuration loaded successfully")
        print(f"   - Summarizer type: {config.summarizer_type}")
        print(f"   - Fetch interval: {config.fetch_interval_minutes} minutes")
        print(f"   - Database path: {config.database_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_optional_dependencies():
    """Test optional dependencies."""
    print("\n🔧 Testing optional dependencies...")
    
    # Test local model dependencies
    try:
        import torch
        print("✅ PyTorch available")
        print(f"   - Version: {torch.__version__}")
    except ImportError:
        print("⚠️  PyTorch not available (needed for local models)")
    
    try:
        import transformers
        print("✅ Transformers available")
        print(f"   - Version: {transformers.__version__}")
    except ImportError:
        print("⚠️  Transformers not available (needed for local models)")
    
    try:
        import bitsandbytes
        print("✅ BitsAndBytes available (quantization support)")
    except ImportError:
        print("ℹ️  BitsAndBytes not available (optional for quantization)")

def test_system_info():
    """Display system information."""
    print("\n💻 System Information...")
    
    try:
        import platform
        import psutil
        
        print(f"   - Platform: {platform.platform()}")
        print(f"   - Architecture: {platform.machine()}")
        print(f"   - Python version: {sys.version}")
        print(f"   - CPU cores: {psutil.cpu_count()}")
        print(f"   - Total RAM: {psutil.virtual_memory().total / (1024**3):.1f}GB")
        print(f"   - Available RAM: {psutil.virtual_memory().available / (1024**3):.1f}GB")
        
        # Check if running on Raspberry Pi
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    print("🍓 Raspberry Pi detected!")
        except FileNotFoundError:
            pass
        
        # Check temperature (Pi specific)
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read()) / 1000.0
                print(f"   - CPU Temperature: {temp:.1f}°C")
        except FileNotFoundError:
            pass
            
    except ImportError as e:
        print(f"❌ Could not get system info: {e}")

def test_model_optimizer():
    """Test the model optimizer utility."""
    print("\n🤖 Testing model optimizer...")
    
    try:
        from ai_news_bot.utils.model_optimizer import ModelOptimizer
        
        optimizer = ModelOptimizer()
        config = optimizer.get_optimal_config()
        
        print("✅ Model optimizer working")
        print(f"   - Recommended tier: {config['tier']}")
        print(f"   - Recommended model: {config['recommended_model']}")
        print(f"   - Recommended precision: {config['precision']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model optimizer test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🤖 AI News Aggregator - Installation Test")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_config()
    test_optional_dependencies()
    test_system_info()
    all_passed &= test_model_optimizer()
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All tests passed! Installation looks good.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your API keys")
        print("2. Run: poetry run ai-news-bot")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure you ran: poetry install")
        print("2. For local models: poetry install --extras local-models")
        print("3. Check that all required environment variables are set")
        
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())