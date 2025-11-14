import scrapy
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
from wechat_spider.items import WechatArticleItem


class WechatSpider(scrapy.Spider):
    name = 'wechat'
    allowed_domains = ['mp.weixin.qq.com']
    
    def __init__(self, account_name='冬日焰火', *args, **kwargs):
        super(WechatSpider, self).__init__(*args, **kwargs)
        self.account_name = account_name
        self.base_url = 'https://mp.weixin.qq.com'
        self.search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz'
        self.article_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://mp.weixin.qq.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    def start_requests(self):
        """Start by searching for the WeChat account"""
        # First, search for the account to get its fake ID
        search_params = {
            'action': 'search_biz',
            'query': self.account_name,
            'begin': 0,
            'count': 5,
            'f': 'json',
            'ajax': 1
        }
        
        yield scrapy.Request(
            url=self.search_url,
            method='GET',
            headers=self.headers,
            callback=self.parse_account_search,
            meta={'params': search_params}
        )
    
    def parse_account_search(self, response):
        """Parse the account search results to get the fake ID"""
        try:
            data = json.loads(response.text)
            if data.get('success') and data.get('list'):
                # Find the matching account
                for account in data['list']:
                    if self.account_name in account.get('nickname', ''):
                        fake_id = account.get('fakeid')
                        if fake_id:
                            self.logger.info(f'Found account: {account.get("nickname")} with fake_id: {fake_id}')
                            # Start crawling articles from this account
                            yield self.create_article_request(fake_id, begin=0)
                            break
                else:
                    self.logger.error(f'Account "{self.account_name}" not found in search results')
            else:
                self.logger.error(f'Failed to search for account: {data}')
        except json.JSONDecodeError as e:
            self.logger.error(f'Failed to parse search response: {e}')
    
    def create_article_request(self, fake_id, begin=0):
        """Create a request to fetch articles from a specific account"""
        params = {
            'action': 'list_ex',
            'begin': begin,
            'count': 5,
            'fakeid': fake_id,
            'type': 9,
            'query': '',
            'token': self.get_token(),
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': 1
        }
        
        url = f"{self.article_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
        
        return scrapy.Request(
            url=url,
            method='GET',
            headers=self.headers,
            callback=self.parse_article_list,
            meta={'fake_id': fake_id, 'begin': begin}
        )
    
    def parse_article_list(self, response):
        """Parse the list of articles and extract individual article URLs"""
        try:
            data = json.loads(response.text)
            
            if data.get('success') and data.get('app_msg_list'):
                articles = data['app_msg_list']
                fake_id = response.meta['fake_id']
                begin = response.meta['begin']
                
                # Process each article
                for article_data in articles:
                    item = self.parse_article_data(article_data, fake_id)
                    if item:
                        # Request the full article content
                        yield scrapy.Request(
                            url=item['url'],
                            method='GET',
                            headers=self.headers,
                            callback=self.parse_article_content,
                            meta={'item': item}
                        )
                
                # Check if there are more articles to fetch
                total_count = data.get('total_page_cnt', 0)
                current_count = begin + len(articles)
                
                if current_count < total_count:
                    # Fetch next batch
                    yield self.create_article_request(fake_id, begin=current_count)
                else:
                    self.logger.info(f'Finished crawling all articles for account: {self.account_name}')
            else:
                self.logger.error(f'Failed to get article list: {data}')
                
        except json.JSONDecodeError as e:
            self.logger.error(f'Failed to parse article list response: {e}')
    
    def parse_article_data(self, article_data, fake_id):
        """Parse basic article data from the list response"""
        try:
            item = WechatArticleItem()
            
            # Basic information
            item['title'] = article_data.get('title', '').strip()
            item['description'] = article_data.get('digest', '').strip()
            item['url'] = article_data.get('link', '')
            item['article_id'] = article_data.get('itemid', '')
            item['digest'] = article_data.get('digest', '')
            
            # Account information
            item['account_name'] = article_data.get('show_name', self.account_name)
            item['account_id'] = fake_id
            item['author'] = article_data.get('author', '')
            
            # Publication information
            item['publish_time'] = self.parse_timestamp(article_data.get('create_time', 0))
            item['cover_image'] = article_data.get('cover', '')
            
            # Statistics
            item['read_count'] = article_data.get('read_num', 0)
            item['like_count'] = article_data.get('like_num', 0)
            item['comment_count'] = article_data.get('comment_cnt', 0)
            
            # Additional metadata
            item['is_original'] = article_data.get('is_multi', 0) == 0
            item['source_url'] = article_data.get('source_url', '')
            
            # Extract tags from title or content if available
            item['tags'] = self.extract_tags(item['title'])
            item['category'] = self.categorize_article(item['title'], item['description'])
            
            return item
            
        except Exception as e:
            self.logger.error(f'Error parsing article data: {e}')
            return None
    
    def parse_article_content(self, response):
        """Parse the full article content from the article page"""
        item = response.meta['item']
        
        try:
            # Extract content using various selectors
            content_selectors = [
                '#js_content',
                '.rich_media_content',
                '.content',
                'article'
            ]
            
            content = ''
            for selector in content_selectors:
                content_element = response.css(selector)
                if content_element:
                    content = content_element.get()
                    break
            
            if content:
                # Clean up HTML content
                content = self.clean_html_content(content)
                item['content'] = content
                
                # Extract images from content
                item['images'] = self.extract_images(response)
                
                # Extract videos if any
                item['videos'] = self.extract_videos(response)
            
            # Update crawl time
            item['crawl_time'] = datetime.now()
            
            self.logger.info(f'Successfully parsed article: {item["title"]}')
            yield item
            
        except Exception as e:
            self.logger.error(f'Error parsing article content for {item.get("title", "unknown")}: {e}')
            # Still yield the item even if content parsing fails
            yield item
    
    def clean_html_content(self, html_content):
        """Clean HTML content and extract text"""
        # Remove HTML tags but keep text content
        import re
        # Remove script and style tags
        html_content = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style.*?>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Replace common HTML tags with newlines
        html_content = re.sub(r'<br[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<p[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</p>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<div[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</div>', '\n', html_content, flags=re.IGNORECASE)
        
        # Remove all remaining HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Clean up whitespace
        html_content = re.sub(r'\n\s*\n', '\n\n', html_content)
        html_content = html_content.strip()
        
        return html_content
    
    def extract_images(self, response):
        """Extract image URLs from the article"""
        images = []
        
        # Extract from img tags
        img_tags = response.css('img')
        for img in img_tags:
            src = img.css('::attr(data-src)').get() or img.css('::attr(src)').get()
            if src:
                # Convert relative URLs to absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.base_url, src)
                images.append(src)
        
        return list(set(images))  # Remove duplicates
    
    def extract_videos(self, response):
        """Extract video URLs from the article"""
        videos = []
        
        # Extract from video tags
        video_tags = response.css('video')
        for video in video_tags:
            src = video.css('::attr(src)').get()
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.base_url, src)
                videos.append(src)
        
        return list(set(videos))  # Remove duplicates
    
    def extract_tags(self, title):
        """Extract tags from article title"""
        # Simple tag extraction based on common keywords
        tags = []
        common_tags = [
            '技术', '教程', '分享', '经验', '总结', '分析', '研究', '开发',
            '设计', '产品', '运营', '营销', '创业', '投资', '职场', '管理',
            '生活', '健康', '教育', '文化', '艺术', '娱乐', '体育', '旅游'
        ]
        
        title_lower = title.lower()
        for tag in common_tags:
            if tag in title_lower:
                tags.append(tag)
        
        return tags
    
    def categorize_article(self, title, description):
        """Categorize article based on title and description"""
        text = (title + ' ' + description).lower()
        
        categories = {
            '技术': ['技术', '编程', '开发', '代码', '算法', '框架', '工具'],
            '生活': ['生活', '日常', '经验', '分享', '故事', '感悟'],
            '教育': ['教育', '学习', '教程', '培训', '知识', '技能'],
            '商业': ['商业', '创业', '投资', '营销', '管理', '职场'],
            '文化': ['文化', '艺术', '历史', '文学', '音乐', '电影'],
            '健康': ['健康', '医疗', '运动', '养生', '心理'],
            '科技': ['科技', '科学', '创新', '未来', '人工智能', '互联网']
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return '其他'
    
    def parse_timestamp(self, timestamp):
        """Parse Unix timestamp to datetime"""
        try:
            return datetime.fromtimestamp(int(timestamp))
        except (ValueError, TypeError):
            return datetime.now()
    
    def get_token(self):
        """Get token for WeChat API requests"""
        # In a real implementation, you would need to extract this from the page
        # or use a more sophisticated authentication method
        return '1234567890'  # Placeholder token
