#!/usr/bin/env python3
"""
Elasticsearch Setup Script for WeChat Crawler
This script sets up Elasticsearch index with proper mappings and settings.
"""

import elasticsearch
import os
from dotenv import load_dotenv

load_dotenv()

def setup_elasticsearch():
    """Setup Elasticsearch index with proper mappings"""
    try:
        # Connect to Elasticsearch
        es_uri = os.getenv('ELASTICSEARCH_URI', 'http://localhost:9200/')
        es = elasticsearch.Elasticsearch([es_uri])
        
        # Index name
        index_name = 'wechat_articles'
        
        print(f"Setting up Elasticsearch index: {index_name}")
        
        # Check if index exists
        if es.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists. Deleting it...")
            es.indices.delete(index=index_name)
            print("Old index deleted.")
        
        # Define index settings and mappings
        index_settings = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "ik_max_word_analyzer": {
                            "type": "custom",
                            "tokenizer": "ik_max_word",
                            "filter": ["lowercase", "stop"]
                        },
                        "ik_smart_analyzer": {
                            "type": "custom", 
                            "tokenizer": "ik_smart",
                            "filter": ["lowercase", "stop"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "ik_max_word_analyzer",
                        "search_analyzer": "ik_smart_analyzer",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "ik_max_word_analyzer",
                        "search_analyzer": "ik_smart_analyzer"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "ik_max_word_analyzer",
                        "search_analyzer": "ik_smart_analyzer"
                    },
                    "author": {
                        "type": "keyword",
                        "fields": {
                            "text": {
                                "type": "text",
                                "analyzer": "ik_max_word_analyzer"
                            }
                        }
                    },
                    "account_name": {
                        "type": "keyword",
                        "fields": {
                            "text": {
                                "type": "text",
                                "analyzer": "ik_max_word_analyzer"
                            }
                        }
                    },
                    "account_id": {
                        "type": "keyword"
                    },
                    "publish_time": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                    "crawl_time": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                    "read_count": {
                        "type": "integer"
                    },
                    "like_count": {
                        "type": "integer"
                    },
                    "comment_count": {
                        "type": "integer"
                    },
                    "cover_image": {
                        "type": "keyword",
                        "index": False
                    },
                    "images": {
                        "type": "keyword",
                        "index": False
                    },
                    "videos": {
                        "type": "keyword",
                        "index": False
                    },
                    "url": {
                        "type": "keyword",
                        "index": False
                    },
                    "article_id": {
                        "type": "keyword"
                    },
                    "digest": {
                        "type": "text",
                        "analyzer": "ik_max_word_analyzer"
                    },
                    "source_url": {
                        "type": "keyword",
                        "index": False
                    },
                    "tags": {
                        "type": "keyword"
                    },
                    "category": {
                        "type": "keyword"
                    },
                    "is_original": {
                        "type": "boolean"
                    }
                }
            }
        }
        
        # Create index
        es.indices.create(index=index_name, body=index_settings)
        print(f"Index '{index_name}' created successfully!")
        
        # Create a sample document to test the setup
        sample_doc = {
            "title": "示例文章",
            "content": "这是一个用于测试Elasticsearch设置的示例文章内容。",
            "description": "示例描述",
            "author": "测试作者",
            "account_name": "测试公众号",
            "account_id": "test_account_001",
            "publish_time": "2024-01-01T00:00:00",
            "crawl_time": "2024-01-01T00:00:00",
            "read_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "cover_image": "",
            "images": [],
            "videos": [],
            "url": "https://example.com/sample",
            "article_id": "sample_001",
            "digest": "示例摘要",
            "source_url": "",
            "tags": ["测试", "示例"],
            "category": "技术",
            "is_original": True
        }
        
        # Index sample document
        es.index(index=index_name, id=sample_doc["article_id"], body=sample_doc)
        print("Sample document indexed successfully!")
        
        # Test the setup
        print("\nTesting Elasticsearch setup...")
        
        # Get index mapping
        mapping = es.indices.get_mapping(index=index_name)
        print(f"Index mapping for '{index_name}':")
        print(f"  Properties: {list(mapping[index_name]['mappings']['properties'].keys())}")
        
        # Test search
        search_result = es.search(
            index=index_name,
            body={
                "query": {
                    "match": {
                        "title": "示例"
                    }
                }
            }
        )
        
        print(f"\nSearch test results:")
        print(f"  Total hits: {search_result['hits']['total']['value']}")
        if search_result['hits']['hits']:
            print(f"  First hit score: {search_result['hits']['hits'][0]['_score']}")
        
        # Remove sample document
        es.delete(index=index_name, id=sample_doc["article_id"])
        print("Sample document removed!")
        
        # Get cluster health
        health = es.cluster.health()
        print(f"\nCluster health: {health['status']}")
        print(f"Number of nodes: {health['number_of_nodes']}")
        
        print("\nElasticsearch setup completed successfully!")
        return True
        
    except elasticsearch.ConnectionError as e:
        print(f"Error connecting to Elasticsearch: {e}")
        print("Please make sure Elasticsearch is running and accessible.")
        return False
    except Exception as e:
        print(f"Error setting up Elasticsearch: {e}")
        return False
    finally:
        if 'es' in locals():
            es.close()

if __name__ == "__main__":
    success = setup_elasticsearch()
    if success:
        print("✅ Elasticsearch is ready for use!")
    else:
        print("❌ Elasticsearch setup failed!")
        exit(1)
