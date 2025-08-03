#!/usr/bin/env python3
"""
Quick SSL certificate fix for AI News Aggregator on macOS.

This script helps fix SSL certificate issues that prevent the bot from
fetching news from HTTPS sites.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def fix_macos_certificates():
    """Fix SSL certificates on macOS."""
    print("🍎 Fixing macOS SSL certificates...")
    
    # Method 1: Try the Install Certificates command
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    cert_command_paths = [
        f"/Applications/Python {python_version}/Install Certificates.command",
        f"/Applications/Python\\ {python_version}/Install\\ Certificates.command",
        "/usr/bin/python3 -m pip install --upgrade certifi"
    ]
    
    for cert_path in cert_command_paths:
        if os.path.exists(cert_path.replace("\\", "")):
            print(f"Running: {cert_path}")
            try:
                subprocess.run(cert_path, shell=True, check=True)
                print("✅ Certificate installation completed")
                return True
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Certificate command failed: {e}")
                continue
    
    # Method 2: Update certifi package
    print("Updating certifi package...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "certifi"], 
                      check=True)
        print("✅ Certifi updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Certifi update failed: {e}")
    
    # Method 3: Install ca-certificates with Homebrew (if available)
    if subprocess.which("brew"):
        print("Installing ca-certificates with Homebrew...")
        try:
            subprocess.run(["brew", "install", "ca-certificates"], check=True)
            subprocess.run(["brew", "link", "--overwrite", "ca-certificates"], check=True)
            print("✅ Homebrew certificates installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Homebrew certificate installation failed: {e}")
    
    return False


def create_temp_ssl_config():
    """Create temporary SSL bypass configuration."""
    print("🔧 Creating temporary SSL bypass configuration...")
    
    env_file = Path(".env")
    
    # Read existing .env or create new one
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Add SSL bypass if not already present
    if "SSL_VERIFY" not in env_content:
        env_content += "\n# Temporary SSL bypass (REMOVE for production!)\n"
        env_content += "SSL_VERIFY=false\n"
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ Added SSL_VERIFY=false to .env file")
        print("⚠️  WARNING: This reduces security - only use for testing!")
        print("⚠️  Remove this setting after fixing SSL certificates!")
        return True
    else:
        print("ℹ️  SSL configuration already present in .env")
        return False


def test_ssl_fix():
    """Test if SSL fix worked."""
    print("🧪 Testing SSL fix...")
    
    try:
        import ssl
        import urllib.request
        
        # Test with a simple HTTPS request
        context = ssl.create_default_context()
        
        # Test basic SSL connectivity
        with urllib.request.urlopen('https://httpbin.org/ip', context=context, timeout=10) as response:
            if response.status == 200:
                print("✅ SSL fix successful!")
                return True
    except Exception as e:
        print(f"❌ SSL test failed: {e}")
        return False
    
    return False


def main():
    """Main fix routine."""
    print("🔧 AI News Aggregator - SSL Certificate Fix")
    print("=" * 50)
    
    system = platform.system()
    print(f"Operating System: {system}")
    print(f"Python Version: {sys.version}")
    
    if system == "Darwin":  # macOS
        print("\n🍎 Detected macOS")
        
        # Try to fix certificates
        if fix_macos_certificates():
            # Test the fix
            if test_ssl_fix():
                print("\n🎉 SSL certificates fixed successfully!")
                print("You can now run: poetry run ai-news-bot")
                return 0
            else:
                print("\n⚠️  Certificate fix didn't work, creating bypass...")
                create_temp_ssl_config()
        else:
            print("\n⚠️  Could not fix certificates automatically")
            create_temp_ssl_config()
    
    elif system == "Linux":
        print("\n🐧 Detected Linux")
        print("Try running:")
        print("sudo apt update && sudo apt install ca-certificates")
        print("poetry run pip install --upgrade certifi")
        
        # Create bypass config
        create_temp_ssl_config()
    
    else:
        print(f"\n❓ Unsupported system: {system}")
        create_temp_ssl_config()
    
    print("\n📝 Next Steps:")
    print("1. Try running the bot: poetry run ai-news-bot")
    print("2. If it works, the SSL bypass is active")
    print("3. For production, fix SSL properly and remove SSL_VERIFY=false")
    print("4. Run connectivity test: poetry run python test_connectivity.py")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nFix cancelled by user")
        sys.exit(1)