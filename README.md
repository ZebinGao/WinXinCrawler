# 微信公众号文章爬虫系统

一个基于 Flask、Flask-SocketIO、Vue.js、Scrapy、MongoDB 和 Elasticsearch 的高可用性微信公众号文章爬取系统。

## 🚀 功能特性

- **实时爬取监控**: 使用 Flask-SocketIO 实现实时进度更新
- **现代化界面**: 基于 Vue.js 3 和 Tailwind CSS 的响应式 UI
- **高效爬取**: 使用 Scrapy 框架进行高效数据爬取
- **数据存储**: MongoDB 用于数据持久化存储
- **全文搜索**: Elasticsearch 提供强大的全文搜索功能
- **智能分类**: 自动对文章进行分类和标签提取
- **实时更新**: WebSocket 连接提供实时状态更新

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue.js 前端   │    │  Flask 后端     │    │   Scrapy 爬虫   │
│                 │    │                 │    │                 │
│ - 实时界面      │◄──►│ - REST API      │◄──►│ - 数据爬取      │
│ - 进度监控      │    │ - WebSocket     │    │ - 内容解析      │
│ - 搜索过滤      │    │ - 任务管理      │    │ - 数据清洗      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │    MongoDB      │    │  Elasticsearch  │
                       │                 │    │                 │
                       │ - 数据存储      │    │ - 全文搜索      │
                       │ - 索引优化      │    │ - 中文分词      │
                       │ - 数据去重      │    │ - 相关性排序    │
                       └─────────────────┘    └─────────────────┘
```

## 📋 系统要求

- Python 3.8+
- MongoDB 4.0+
- Elasticsearch 7.0+
- Node.js (可选，用于前端开发)

## 🛠️ 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/ZebinGao/WinXinCrawler.git
cd WinXinCrawler
```

### 2. 安装依赖

```bash
python run.py install
```

### 3. 配置环境

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件（根据实际情况修改）
# MONGODB_URI=mongodb://localhost:27017/
# ELASTICSEARCH_URI=http://localhost:9200/
```

### 4. 初始化系统

```bash
# 完整设置（包括数据库初始化）
python run.py setup

# 或者跳过某些组件
python run.py setup --skip-mongo --skip-elasticsearch
```

### 5. 启动系统

```bash
python run.py start
```

访问 http://localhost:5000 查看系统界面。

## 📖 使用说明

### 命令行工具

```bash
# 检查依赖
python run.py check

# 测试系统
python run.py test

# 直接运行爬虫
python run.py crawl --account "冬日焰火"

# 启动 Web 服务
python run.py start
```

### Web 界面功能

1. **控制面板**
   - 输入公众号名称
   - 启动/停止爬取任务
   - 实时查看爬取进度

2. **文章管理**
   - 浏览所有爬取的文章
   - 搜索文章内容
   - 按分类筛选
   - 查看文章详情

3. **实时监控**
   - 爬取进度条
   - 当前处理文章
   - 状态更新

## 🔧 配置说明

### 环境变量 (.env)

```bash
# Flask 配置
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# MongoDB 配置
MONGODB_URI=mongodb://localhost:27017/

# Elasticsearch 配置
ELASTICSEARCH_URI=http://localhost:9200/

# 爬虫配置
WECHAT_ACCOUNT=冬日焰火
CRAWL_DELAY=2
MAX_CONCURRENT_REQUESTS=1
```

### Scrapy 配置

主要配置文件：`wechat_spider/settings.py`

- `DOWNLOAD_DELAY`: 请求延迟（秒）
- `CONCURRENT_REQUESTS`: 并发请求数
- `ITEM_PIPELINES`: 数据处理管道

## 📊 数据结构

### 文章数据模型

```json
{
  "title": "文章标题",
  "content": "文章内容",
  "description": "文章描述",
  "url": "文章链接",
  "author": "作者",
  "account_name": "公众号名称",
  "publish_time": "发布时间",
  "read_count": "阅读数",
  "like_count": "点赞数",
  "comment_count": "评论数",
  "cover_image": "封面图片",
  "images": ["图片链接数组"],
  "videos": ["视频链接数组"],
  "tags": ["标签数组"],
  "category": "分类",
  "is_original": "是否原创"
}
```

## 🚨 注意事项

1. **合规使用**: 请遵守微信公众号的使用条款和相关法律法规
2. **爬取频率**: 系统已设置合理的爬取延迟，避免对服务器造成压力
3. **数据备份**: 建议定期备份 MongoDB 数据
4. **网络环境**: 确保网络连接稳定，能够访问微信公众号平台

## 🐛 故障排除

### 常见问题

1. **MongoDB 连接失败**
   ```bash
   # 检查 MongoDB 是否运行
   mongosh --eval "db.adminCommand('ismaster')"
   ```

2. **Elasticsearch 连接失败**
   ```bash
   # 检查 Elasticsearch 是否运行
   curl http://localhost:9200/_cluster/health
   ```

   #### __Windows环境下安装Elasticsearch：__

1. __下载Elasticsearch__

   - 访问 [](https://www.elastic.co/downloads/elasticsearch)<https://www.elastic.co/downloads/elasticsearch>
   - 下载Windows版本的ZIP文件
   - 解压到本地目录（如：`C:\elasticsearch-8.11.0`）

2. __配置Elasticsearch__

   - 编辑 `config/elasticsearch.yml` 文件
   - 添加以下配置：

   ```yaml
   network.host: 127.0.0.1
   http.port: 9200
   xpack.security.enabled: false
   ```

3. __启动Elasticsearch__

   ```cmd
   cd C:\elasticsearch-8.11.0\bin
   elasticsearch.bat
   ```


3. **爬虫无法获取数据**
   - 检查网络连接
   - 确认公众号名称正确
   - 查看爬虫日志



### 日志查看

```bash
# 查看爬虫日志
scrapy crawl wechat -L INFO

# 查看 Flask 应用日志
python app.py
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Scrapy](https://scrapy.org/) - 爬虫框架
- [MongoDB](https://www.mongodb.com/) - 数据库
- [Elasticsearch](https://www.elastic.co/) - 搜索引擎
- [Tailwind CSS](https://tailwindcss.com/) - CSS 框架

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/ZebinGao/WinXinCrawler/issues)
- 邮箱: your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给它一个星标！
