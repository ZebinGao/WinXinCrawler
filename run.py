#!/usr/bin/env python3
"""
Main Runner Script for WeChat Crawler
This script provides a command-line interface to manage the crawler system.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'flask', 'flask_socketio', 'scrapy', 'pymongo', 
        'elasticsearch', 'requests', 'beautifulsoup4', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'beautifulsoup4':
                __import__('bs4')
            elif package == 'python-dotenv':
                __import__('dotenv')
            elif package == 'flask_socketio':
                __import__('flask_socketio')
            elif package == 'python-socketio':
                __import__('socketio')
            else:
                __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def setup_environment():
    """Setup environment configuration"""
    print("\n🔧 Setting up environment...")
    
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from .env.example")
            print("⚠️  Please edit .env file with your configuration")
        else:
            print("❌ .env.example file not found!")
            return False
    else:
        print("✅ .env file already exists")
    
    return True

def setup_mongodb():
    """Setup MongoDB database and indexes"""
    print("\n🗄️  Setting up MongoDB...")
    
    try:
        result = subprocess.run([sys.executable, 'setup_mongodb.py'], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ MongoDB setup failed: {e.stderr}")
        return False

def setup_elasticsearch():
    """Setup Elasticsearch index and mappings"""
    print("\n🔍 Setting up Elasticsearch...")
    
    try:
        result = subprocess.run([sys.executable, 'setup_elasticsearch.py'], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Elasticsearch setup failed: {e.stderr}")
        return False

def start_web_server():
    """Start the Flask web server"""
    print("\n🚀 Starting web server...")
    
    try:
        # Set environment variables for development
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        
        # Start the Flask app
        subprocess.run([sys.executable, 'app.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start web server: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Web server stopped by user")
        return True

def run_crawler(account_name='冬日焰火'):
    """Run the Scrapy crawler directly"""
    print(f"\n🕷️  Running crawler for account: {account_name}")
    
    try:
        cmd = [sys.executable, '-m', 'scrapy', 'crawl', 'wechat', 
               '-a', f'account_name={account_name}']
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Crawler failed: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Crawler stopped by user")
        return True

def test_system():
    """Test the complete system setup"""
    print("\n🧪 Testing system setup...")
    
    # Test imports
    try:
        import flask
        import scrapy
        import pymongo
        import elasticsearch
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test database connections
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Test MongoDB
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        mongo_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        mongo_client.server_info()
        print("✅ MongoDB connection successful")
        mongo_client.close()
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False
    
    try:
        # Test Elasticsearch
        es_uri = os.getenv('ELASTICSEARCH_URI', 'http://localhost:9200/')
        es_client = elasticsearch.Elasticsearch([es_uri])
        es_client.cluster.health(timeout='2s')
        print("✅ Elasticsearch connection successful")
        es_client.close()
    except Exception as e:
        print(f"❌ Elasticsearch connection failed: {e}")
        return False
    
    print("✅ System test completed successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description='WeChat Article Crawler Management System')
    parser.add_argument('command', choices=[
        'setup', 'start', 'crawl', 'test', 'check', 'install'
    ], help='Command to execute')
    parser.add_argument('--account', default='冬日焰火', 
                       help='WeChat account name to crawl (default: 冬日焰火)')
    parser.add_argument('--skip-mongo', action='store_true',
                       help='Skip MongoDB setup')
    parser.add_argument('--skip-elasticsearch', action='store_true',
                       help='Skip Elasticsearch setup')
    
    args = parser.parse_args()
    
    print("🕷️  WeChat Article Crawler Management System")
    print("=" * 50)
    
    if args.command == 'install':
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        return
    
    elif args.command == 'check':
        check_dependencies()
        return
    
    elif args.command == 'setup':
        print("🔧 Setting up WeChat Crawler System...")
        
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)
        
        # Setup environment
        if not setup_environment():
            sys.exit(1)
        
        # Setup MongoDB
        if not args.skip_mongo:
            if not setup_mongodb():
                print("⚠️  MongoDB setup failed, but you can continue without it")
        
        # Setup Elasticsearch
        if not args.skip_elasticsearch:
            if not setup_elasticsearch():
                print("⚠️  Elasticsearch setup failed, but you can continue without it")
        
        print("\n✅ Setup completed!")
        print("You can now run: python run.py start")
        
    elif args.command == 'test':
        test_system()
        
    elif args.command == 'crawl':
        if not check_dependencies():
            sys.exit(1)
        run_crawler(args.account)
        
    elif args.command == 'start':
        if not check_dependencies():
            sys.exit(1)
        start_web_server()

if __name__ == "__main__":
    main()
