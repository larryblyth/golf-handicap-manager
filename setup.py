#!/usr/bin/env python3
"""
Setup script for Golf Handicap Manager Gmail integration
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing Gmail API dependencies...")

    requirements = [
        "google-api-python-client==2.108.0",
        "google-auth-httplib2==0.1.1",
        "google-auth-oauthlib==1.1.0",
        "beautifulsoup4==4.12.2"
    ]

    for requirement in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", requirement])
            print(f"✅ Installed {requirement}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {requirement}: {e}")
            return False

    return True

def setup_env_file():
    """Create .env file from example if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from example")
            print("📝 Please edit .env file with your Google OAuth credentials")
        else:
            print("❌ .env.example file not found")
    else:
        print("✅ .env file already exists")

def main():
    print("🏌️ Setting up Golf Handicap Manager Gmail Integration")
    print("=" * 60)

    if install_requirements():
        print("\n✅ All dependencies installed successfully!")
    else:
        print("\n❌ Failed to install some dependencies")
        return 1

    setup_env_file()

    print("\n🎯 Setup Instructions:")
    print("1. Edit .env file with your Google OAuth credentials")
    print("2. Go to https://console.cloud.google.com/")
    print("3. Create OAuth 2.0 credentials")
    print("4. Add http://localhost:8000/api/oauth-callback as redirect URI")
    print("5. Run: python3 server.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())