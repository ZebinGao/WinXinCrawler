from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import json
import threading
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from wechat_spider.spiders.wechat import WechatSpider
import pymongo
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# MongoDB connection
mongo_client = pymongo.MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
db = mongo_client['wechat_crawler']
articles_collection = db['articles']

# Elasticsearch connection
es = Elasticsearch([os.getenv('ELASTICSEARCH_URI', 'http://localhost:9200/')])

class CrawlerManager:
    def __init__(self):
        self.is_running = False
        self.current_task = None
        self.progress = 0
        self.total_articles = 0
        self.crawled_articles = 0
        
    def start_crawling(self, account_name):
        if self.is_running:
            return False, "Crawler is already running"
        
        self.is_running = True
        self.current_task = account_name
        self.progress = 0
        self.crawled_articles = 0
        
        # Start crawling in a separate thread
        thread = threading.Thread(target=self._crawl_articles, args=(account_name,))
        thread.daemon = True
        thread.start()
        
        return True, "Crawling started"
    
    def _crawl_articles(self, account_name):
        try:
            settings = get_project_settings()
            settings.set('ITEM_PIPELINES', {
                'wechat_spider.pipelines.MongoPipeline': 300,
                'wechat_spider.pipelines.ElasticsearchPipeline': 400,
            })
            
            process = CrawlerProcess(settings)
            
            # Custom spider class with socketio integration
            class SocketIOWechatSpider(WechatSpider):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.crawler_manager = crawler_manager
                
                def process_item(self, item, spider):
                    crawler_manager.crawled_articles += 1
                    progress = (crawler_manager.crawled_articles / max(crawler_manager.total_articles, 1)) * 100
                    crawler_manager.progress = progress
                    
                    socketio.emit('crawl_progress', {
                        'progress': progress,
                        'crawled': crawler_manager.crawled_articles,
                        'total': crawler_manager.total_articles,
                        'current_article': item.get('title', ''),
                        'status': 'crawling'
                    })
                    
                    return item
            
            process.crawl(SocketIOWechatSpider, account_name=account_name)
            process.start()
            
            self.is_running = False
            socketio.emit('crawl_progress', {
                'progress': 100,
                'crawled': self.crawled_articles,
                'total': self.total_articles,
                'status': 'completed'
            })
            
        except Exception as e:
            self.is_running = False
            socketio.emit('crawl_progress', {
                'progress': self.progress,
                'crawled': self.crawled_articles,
                'total': self.total_articles,
                'status': 'error',
                'error': str(e)
            })

crawler_manager = CrawlerManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_crawl', methods=['POST'])
def start_crawl():
    data = request.json
    account_name = data.get('account_name', '冬日焰火')
    
    success, message = crawler_manager.start_crawling(account_name)
    
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/api/status')
def get_status():
    return jsonify({
        'is_running': crawler_manager.is_running,
        'current_task': crawler_manager.current_task,
        'progress': crawler_manager.progress,
        'crawled_articles': crawler_manager.crawled_articles,
        'total_articles': crawler_manager.total_articles
    })

@app.route('/api/articles')
def get_articles():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search_query = request.args.get('search', '')
    
    query = {}
    if search_query:
        query = {
            '$or': [
                {'title': {'$regex': search_query, '$options': 'i'}},
                {'content': {'$regex': search_query, '$options': 'i'}}
            ]
        }
    
    articles = list(articles_collection.find(query)
                   .sort('publish_time', -1)
                   .skip((page - 1) * per_page)
                   .limit(per_page))
    
    total = articles_collection.count_documents(query)
    
    # Convert ObjectId to string for JSON serialization
    for article in articles:
        article['_id'] = str(article['_id'])
        if 'publish_time' in article:
            article['publish_time'] = article['publish_time'].isoformat()
    
    return jsonify({
        'articles': articles,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@app.route('/api/search')
def search_articles():
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    if not query:
        return jsonify({'articles': [], 'total': 0, 'page': page, 'per_page': per_page})
    
    # Elasticsearch search
    search_body = {
        'query': {
            'multi_match': {
                'query': query,
                'fields': ['title', 'content', 'description']
            }
        },
        'sort': [
            {'publish_time': {'order': 'desc'}}
        ],
        'from': (page - 1) * per_page,
        'size': per_page
    }
    
    try:
        response = es.search(index='wechat_articles', body=search_body)
        hits = response['hits']
        
        articles = []
        for hit in hits['hits']:
            article = hit['_source']
            article['_id'] = hit['_id']
            articles.append(article)
        
        return jsonify({
            'articles': articles,
            'total': hits['total']['value'],
            'page': page,
            'per_page': per_page,
            'total_pages': (hits['total']['value'] + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    emit('status', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=8080)
