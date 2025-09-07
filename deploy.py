#!/usr/bin/env python3
"""
Deployment Script for Medical Management System
This script helps you deploy your application to various platforms
"""

import os
import subprocess
import sys
import json

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'app.py',
        'requirements.txt',
        'Procfile',
        'runtime.txt',
        'firebase-service-account.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files found")
    return True

def test_local():
    """Test the application locally"""
    print("\n🧪 Testing application locally...")
    
    try:
        # Test Firebase connection
        result = subprocess.run([sys.executable, 'test_firebase.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Firebase connection test passed")
        else:
            print("❌ Firebase connection test failed")
            print(result.stdout)
            return False
        
        # Test NodeMCU connection (optional)
        try:
            result = subprocess.run([sys.executable, 'test_nodmcu.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ NodeMCU connection test passed")
            else:
                print("⚠️  NodeMCU connection test failed (this is OK if NodeMCU is not connected)")
        except:
            print("⚠️  NodeMCU test skipped")
        
        return True
        
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        return False

def deploy_heroku():
    """Deploy to Heroku"""
    print("\n🚀 Deploying to Heroku...")
    
    try:
        # Check if Heroku CLI is installed
        result = subprocess.run(['heroku', '--version'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Heroku CLI not found. Please install it first.")
            return False
        
        # Initialize git if not already done
        if not os.path.exists('.git'):
            subprocess.run(['git', 'init'], check=True)
            print("✅ Git repository initialized")
        
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Deploy medical management system'], check=True)
        print("✅ Files committed to git")
        
        # Create Heroku app (if not exists)
        try:
            app_name = input("Enter Heroku app name (or press Enter for auto-generated): ").strip()
            if app_name:
                subprocess.run(['heroku', 'create', app_name], check=True)
            else:
                subprocess.run(['heroku', 'create'], check=True)
            print("✅ Heroku app created")
        except subprocess.CalledProcessError:
            print("⚠️  Heroku app might already exist")
        
        # Set environment variables
        subprocess.run(['heroku', 'config:set', 'FLASK_ENV=production'], check=True)
        subprocess.run(['heroku', 'config:set', 'SECRET_KEY=your-secret-key-change-this'], check=True)
        print("✅ Environment variables set")
        
        # Deploy
        subprocess.run(['git', 'push', 'heroku', 'main'], check=True)
        print("✅ Deployment successful!")
        
        # Get app URL
        result = subprocess.run(['heroku', 'apps:info'], 
                              capture_output=True, text=True)
        print(f"🌐 Your app is available at: https://your-app-name.herokuapp.com")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Heroku deployment failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

def deploy_railway():
    """Deploy to Railway"""
    print("\n🚀 Deploying to Railway...")
    
    print("📋 Railway Deployment Steps:")
    print("1. Go to https://railway.app/")
    print("2. Sign up with GitHub")
    print("3. Click 'New Project' > 'Deploy from GitHub repo'")
    print("4. Select your repository")
    print("5. Railway will automatically detect Python and deploy")
    print("6. Add environment variables in Railway dashboard:")
    print("   - FLASK_ENV=production")
    print("   - SECRET_KEY=your-secret-key")
    
    return True

def setup_environment():
    """Set up environment variables"""
    print("\n🔧 Setting up environment variables...")
    
    env_vars = {
        'FLASK_ENV': 'development',
        'SECRET_KEY': 'your-secret-key-change-this',
        'NODEMCU_IP': '192.168.1.100'
    }
    
    # Create .env file
    with open('.env', 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print("✅ .env file created")
    print("📝 Please update the values in .env file as needed")

def main():
    """Main deployment function"""
    print("=" * 60)
    print("Medical Management System Deployment Script")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please ensure all required files are present before deploying.")
        return
    
    # Setup environment
    setup_environment()
    
    # Test locally
    if not test_local():
        print("\n❌ Local tests failed. Please fix issues before deploying.")
        return
    
    # Choose deployment option
    print("\n" + "=" * 60)
    print("Choose deployment option:")
    print("1. Deploy to Heroku")
    print("2. Deploy to Railway (manual)")
    print("3. Run locally only")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        deploy_heroku()
    elif choice == '2':
        deploy_railway()
    elif choice == '3':
        print("\n🏃 Running application locally...")
        print("Run: python app.py")
        print("Then visit: http://localhost:5000")
    elif choice == '4':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")
    
    print("\n" + "=" * 60)
    print("🎉 Deployment process completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
