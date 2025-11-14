import scrapy
from datetime import datetime


class WechatArticleItem(scrapy.Item):
    # Basic article information
    title = scrapy.Field()
    content = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    
    # Author and account information
    author = scrapy.Field()
    account_name = scrapy.Field()
    account_id = scrapy.Field()
    
    # Publication information
    publish_time = scrapy.Field()
    read_count = scrapy.Field()
    like_count = scrapy.Field()
    comment_count = scrapy.Field()
    
    # Media information
    cover_image = scrapy.Field()
    images = scrapy.Field()
    videos = scrapy.Field()
    
    # Metadata
    crawl_time = scrapy.Field()
    article_id = scrapy.Field()
    digest = scrapy.Field()
    source_url = scrapy.Field()
    
    # Additional fields
    tags = scrapy.Field()
    category = scrapy.Field()
    is_original = scrapy.Field()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default crawl time
        self['crawl_time'] = datetime.now()
