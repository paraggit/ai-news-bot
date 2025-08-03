#!/usr/bin/env python3
"""
Test script to verify network connectivity and SSL certificates.

This script helps diagnose and fix SSL certificate issues on macOS.
"""

import asyncio
import ssl
import sys
import platform
from typing import List, Dict, Any

import aiohttp
import certifi


async def test_basic_connectivity() -> bool:
    """Test basic internet connectivity."""
    print("🌐 Testing basic connectivity...")
    
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get('http://httpbin.org/ip') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Basic connectivity OK (IP: {data.get('origin', 'unknown')})")
                    return True
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
        return False
    
    return False


async def test_ssl_connectivity() -> Dict[str, bool]:
    """Test SSL connectivity to various sites."""
    print("\n🔒 Testing SSL connectivity...")
    
    test_sites = [
        "https://httpbin.org/ip",
        "https://api.github.com",
        "https://techcrunch.com",
        "https://export.arxiv.org",
        "https://openai.com"
    ]
    
    results = {}
    
    # Test with system certificates
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
    timeout = aiohttp.ClientTimeout(total=15)
    
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for site in test_sites:
                try:
                    async with session.get(site) as response:
                        if response.status < 400:
                            print(f"✅ {site} - OK ({response.status})")
                            results[site] = True
                        else:
                            print(f"⚠️  {site} - HTTP {response.status}")
                            results[site] = False
                except Exception as e:
                    print(f"❌ {site} - Failed: {e}")
                    results[site] = False
    except Exception as e:
        print(f"❌ SSL session creation failed: {e}")
        for site in test_sites:
            results[site] = False
    
    return results


async def test_rss_feeds() -> Dict[str, bool]:
    """Test RSS feed connectivity."""
    print("\n📰 Testing RSS feeds...")
    
    rss_feeds = [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/ai/feed/",
        "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
        "https://www.wired.com/tag/artificial-intelligence/feed/",
        "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"
    ]
    
    results = {}
    
    # Try with relaxed SSL for testing
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
    timeout = aiohttp.ClientTimeout(total=20)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; AI-News-Bot/1.0; +https://example.com/bot)',
        'Accept': 'application/rss+xml, application/xml, text/xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout, 
            headers=headers
        ) as session:
            for feed in rss_feeds:
                try:
                    async with session.get(feed) as response:
                        if response.status == 200:
                            content = await response.text()
                            if 'xml' in content[:200].lower() or 'rss' in content[:200].lower():
                                print(f"✅ {feed} - Valid RSS")
                                results[feed] = True
                            else:
                                print(f"⚠️  {feed} - Not RSS format")
                                results[feed] = False
                        else:
                            print(f"❌ {feed} - HTTP {response.status}")
                            results[feed] = False
                except Exception as e:
                    print(f"❌ {feed} - Failed: {str(e)[:100]}...")
                    results[feed] = False
    except Exception as e:
        print(f"❌ RSS session creation failed: {e}")
        for feed in rss_feeds:
            results[feed] = False
    
    return results


def check_system_certificates():
    """Check system certificate configuration."""
    print("\n🔐 Checking certificate configuration...")
    
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python version: {sys.version}")
    
    # Check certifi
    try:
        cert_path = certifi.where()
        print(f"✅ Certifi certificates found: {cert_path}")
        
        # Check if file exists and is readable
        with open(cert_path, 'r') as f:
            cert_count = f.read().count('BEGIN CERTIFICATE')
            print(f"📊 Certificate count: {cert_count}")
    except Exception as e:
        print(f"❌ Certifi issue: {e}")
    
    # macOS specific checks
    if platform.system() == "Darwin":
        print("\n🍎 macOS SSL Configuration:")
        print("If you're seeing SSL errors, try these fixes:")
        print("1. Update certificates: /Applications/Python\\ 3.x/Install\\ Certificates.command")
        print("2. Or run: pip install --upgrade certifi")
        print("3. For system Python: brew install ca-certificates")
        
        # Check for common certificate issues
        try:
            import subprocess
            result = subprocess.run(['security', 'find-certificate', '-a', '-p'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                cert_count = result.stdout.count('BEGIN CERTIFICATE')
                print(f"📊 System keychain certificates: {cert_count}")
            else:
                print("⚠️  Could not access system keychain")
        except Exception:
            print("⚠️  Could not check system certificates")


def print_ssl_fix_instructions():
    """Print instructions for fixing SSL issues."""
    print("\n🔧 SSL Certificate Fix Instructions:")
    print("=" * 50)
    
    if platform.system() == "Darwin":
        print("For macOS:")
        print("1. Install certificates for your Python installation:")
        print("   /Applications/Python\\ 3.x/Install\\ Certificates.command")
        print("")
        print("2. Or update certifi package:")
        print("   poetry run pip install --upgrade certifi")
        print("")
        print("3. If using Homebrew Python:")
        print("   brew install ca-certificates")
        print("   brew link --overwrite ca-certificates")
        print("")
        print("4. Alternative - use system certificates:")
        print("   export SSL_CERT_FILE=/etc/ssl/cert.pem")
        print("   export REQUESTS_CA_BUNDLE=/etc/ssl/cert.pem")
    else:
        print("For Linux:")
        print("1. Update ca-certificates:")
        print("   sudo apt update && sudo apt install ca-certificates")
        print("")
        print("2. Update certifi:")
        print("   poetry run pip install --upgrade certifi")
    
    print("\n5. Test with relaxed SSL (temporary fix):")
    print("   Add SSL_VERIFY=false to your .env file")


async def main():
    """Run all connectivity tests."""
    print("🔍 AI News Aggregator - Connectivity Test")
    print("=" * 50)
    
    # Basic connectivity
    basic_ok = await test_basic_connectivity()
    
    if not basic_ok:
        print("❌ Basic connectivity failed. Check your internet connection.")
        return 1
    
    # SSL connectivity
    ssl_results = await test_ssl_connectivity()
    ssl_success_count = sum(ssl_results.values())
    
    print(f"\n📊 SSL Test Results: {ssl_success_count}/{len(ssl_results)} sites accessible")
    
    # RSS feeds
    rss_results = await test_rss_feeds()
    rss_success_count = sum(rss_results.values())
    
    print(f"📊 RSS Test Results: {rss_success_count}/{len(rss_results)} feeds accessible")
    
    # System certificates
    check_system_certificates()
    
    # Recommendations
    print("\n🎯 Recommendations:")
    
    if ssl_success_count == 0:
        print("❌ SSL completely broken - certificate configuration needed")
        print_ssl_fix_instructions()
    elif ssl_success_count < len(ssl_results) * 0.5:
        print("⚠️  Partial SSL issues - some sites blocked or slow")
        print("- Try running the certificate fix commands")
        print("- Check firewall/proxy settings")
    else:
        print("✅ SSL mostly working - minor connectivity issues")
        print("- Bot should work, some sources might be intermittently unavailable")
    
    if rss_success_count == 0:
        print("❌ No RSS feeds accessible")
        print("- Check if you're behind a corporate firewall")
        print("- Try using API-based summarizers (OpenAI/DeepSeek) instead of local")
    
    # Create temporary config for testing
    print("\n🔧 Temporary workaround:")
    print("Add this to your .env file to bypass SSL issues for testing:")
    print("SSL_VERIFY=false")
    print("Note: This reduces security - only use for testing!")
    
    return 0 if ssl_success_count > 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        sys.exit(1)