#!/usr/bin/env python3
"""
MongoDB Setup Script for WeChat Crawler
This script sets up the MongoDB database and collections with proper indexes.
"""

import pymongo
import os
from dotenv import load_dotenv

load_dotenv()

def setup_mongodb():
    """Setup MongoDB database and collections"""
    try:
        # Connect to MongoDB
        mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        client = pymongo.MongoClient(mongo_uri)
        
        # Create database
        db_name = 'wechat_crawler'
        db = client[db_name]
        
        print(f"Setting up MongoDB database: {db_name}")
        
        # Create articles collection
        articles_collection = db['articles']
        
        # Create indexes for better performance
        print("Creating indexes...")
        
        # Text index for search functionality
        articles_collection.create_index([
            ("title", "text"), 
            ("content", "text"),
            ("description", "text")
        ], name="text_search_index")
        
        # Compound index for account and publish time
        articles_collection.create_index([
            ("account_name", 1),
            ("publish_time", -1)
        ], name="account_publish_time_index")
        
        # Index for article_id (unique)
        articles_collection.create_index([
            ("article_id", 1)
        ], unique=True, name="article_id_unique_index")
        
        # Index for category
        articles_collection.create_index([
            ("category", 1)
        ], name="category_index")
        
        # Index for tags
        articles_collection.create_index([
            ("tags", 1)
        ], name="tags_index")
        
        # Index for publish time
        articles_collection.create_index([
            ("publish_time", -1)
        ], name="publish_time_index")
        
        # Create a sample document to test the setup
        sample_article = {
            "title": "Sample Article",
            "content": "This is a sample article for testing the MongoDB setup.",
            "description": "Sample description",
            "url": "https://example.com/sample",
            "article_id": "sample_001",
            "account_name": "test_account",
            "author": "Test Author",
            "publish_time": "2024-01-01T00:00:00",
            "read_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "cover_image": "",
            "images": [],
            "videos": [],
            "crawl_time": "2024-01-01T00:00:00",
            "digest": "Sample digest",
            "source_url": "",
            "tags": ["test", "sample"],
            "category": "技术",
            "is_original": True
        }
        
        # Insert sample document (will be replaced by real data)
        try:
            articles_collection.insert_one(sample_article)
            print("Sample document inserted successfully")
            # Remove the sample document immediately
            articles_collection.delete_one({"article_id": "sample_001"})
            print("Sample document removed")
        except pymongo.errors.DuplicateKeyError:
            print("Sample document already exists, removing it...")
            articles_collection.delete_one({"article_id": "sample_001"})
        
        # Test the setup
        print("\nTesting MongoDB setup...")
        stats = db.command("dbStats")
        print(f"Database: {stats['db']}")
        print(f"Collections: {stats['collections']}")
        print(f"Data size: {stats['dataSize']} bytes")
        
        # List all indexes
        indexes = articles_collection.list_indexes()
        print("\nCreated indexes:")
        for index in indexes:
            print(f"  - {index['name']}: {index['key']}")
        
        print("\nMongoDB setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error setting up MongoDB: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    success = setup_mongodb()
    if success:
        print("✅ MongoDB is ready for use!")
    else:
        print("❌ MongoDB setup failed!")
        exit(1)
