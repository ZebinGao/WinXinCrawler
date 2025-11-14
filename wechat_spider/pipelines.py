import pymongo
from elasticsearch import Elasticsearch
from datetime import datetime
import logging
from scrapy.exceptions import DropItem


class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.client = None
        self.db = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGODB_URI'),
            mongo_db=crawler.settings.get('MONGODB_DATABASE', 'wechat_crawler')
        )

    def open_spider(self, spider):
        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.mongo_db]
            # Create index for better search performance
            self.db.articles.create_index([("title", "text"), ("content", "text")])
            self.db.articles.create_index([("account_name", 1)])
            self.db.articles.create_index([("publish_time", -1)])
            spider.logger.info('MongoDB connection established')
        except Exception as e:
            spider.logger.error(f'Failed to connect to MongoDB: {e}')

    def close_spider(self, spider):
        if self.client:
            self.client.close()
            spider.logger.info('MongoDB connection closed')

    def process_item(self, item, spider):
        try:
            # Check if article already exists
            existing = self.db.articles.find_one({'article_id': item.get('article_id')})
            if existing:
                spider.logger.debug(f'Article already exists: {item.get("title")}')
                raise DropItem(f"Duplicate item found: {item.get('title')}")
            
            # Convert datetime objects to string for MongoDB
            item_dict = dict(item)
            for key, value in item_dict.items():
                if isinstance(value, datetime):
                    item_dict[key] = value.isoformat()
            
            # Insert into MongoDB
            self.db.articles.insert_one(item_dict)
            spider.logger.info(f'Article saved to MongoDB: {item.get("title")}')
            return item
            
        except Exception as e:
            spider.logger.error(f'Error saving to MongoDB: {e}')
            raise DropItem(f"Error saving item to MongoDB: {e}")


class ElasticsearchPipeline:
    def __init__(self, es_uri, es_index):
        self.es_uri = es_uri
        self.es_index = es_index
        self.es = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            es_uri=crawler.settings.get('ELASTICSEARCH_URI'),
            es_index=crawler.settings.get('ELASTICSEARCH_INDEX', 'wechat_articles')
        )

    def open_spider(self, spider):
        try:
            self.es = Elasticsearch([self.es_uri])
            
            # Create index with mapping if it doesn't exist
            if not self.es.indices.exists(index=self.es_index):
                mapping = {
                    "mappings": {
                        "properties": {
                            "title": {
                                "type": "text",
                                "analyzer": "ik_max_word",
                                "search_analyzer": "ik_smart"
                            },
                            "content": {
                                "type": "text",
                                "analyzer": "ik_max_word",
                                "search_analyzer": "ik_smart"
                            },
                            "description": {
                                "type": "text",
                                "analyzer": "ik_max_word",
                                "search_analyzer": "ik_smart"
                            },
                            "author": {"type": "keyword"},
                            "account_name": {"type": "keyword"},
                            "publish_time": {"type": "date"},
                            "read_count": {"type": "integer"},
                            "like_count": {"type": "integer"},
                            "comment_count": {"type": "integer"},
                            "crawl_time": {"type": "date"},
                            "tags": {"type": "keyword"},
                            "category": {"type": "keyword"},
                            "is_original": {"type": "boolean"}
                        }
                    }
                }
                self.es.indices.create(index=self.es_index, body=mapping)
                spider.logger.info(f'Elasticsearch index {self.es_index} created')
            
            spider.logger.info('Elasticsearch connection established')
            
        except Exception as e:
            spider.logger.error(f'Failed to connect to Elasticsearch: {e}')

    def close_spider(self, spider):
        if self.es:
            self.es.close()
            spider.logger.info('Elasticsearch connection closed')

    def process_item(self, item, spider):
        try:
            # Prepare document for Elasticsearch
            doc = dict(item)
            
            # Convert datetime objects to ISO format
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.isoformat()
            
            # Use article_id as document ID if available
            doc_id = doc.get('article_id')
            
            # Index document
            self.es.index(
                index=self.es_index,
                id=doc_id,
                body=doc
            )
            
            spider.logger.info(f'Article indexed in Elasticsearch: {item.get("title")}')
            return item
            
        except Exception as e:
            spider.logger.error(f'Error indexing in Elasticsearch: {e}')
            # Don't drop the item, just log the error
            return item


class ValidationPipeline:
    def process_item(self, item, spider):
        # Validate required fields
        if not item.get('title'):
            raise DropItem("Missing title in item")
        
        if not item.get('content'):
            raise DropItem("Missing content in item")
        
        if not item.get('url'):
            raise DropItem("Missing url in item")
        
        return item


class CleaningPipeline:
    def process_item(self, item, spider):
        # Clean title
        if item.get('title'):
            item['title'] = item['title'].strip()
        
        # Clean content
        if item.get('content'):
            # Remove extra whitespace
            content = ' '.join(item['content'].split())
            item['content'] = content
        
        # Clean description
        if item.get('description'):
            item['description'] = item['description'].strip()
        
        # Ensure numeric fields are proper types
        for field in ['read_count', 'like_count', 'comment_count']:
            if item.get(field):
                try:
                    item[field] = int(item[field])
                except (ValueError, TypeError):
                    item[field] = 0
        
        return item
