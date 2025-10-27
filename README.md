# Notion API 中转服务

一个简化的 Notion API 中转服务，基于 [notion-mcp-server](https://github.com/makenotion/notion-mcp-server) 提供简化的 REST API 接口。

## 功能特性

- 🔐 简单的 Bearer Token 认证
- 📄 通过 page ID 获取页面完整内容（Markdown 格式）
- 📊 通过 database ID 获取页面列表
- 🔍 全局搜索功能
- 🗃️ Database 内搜索（支持过滤和排序）
- 📝 自动将 Notion blocks 转换为人类可读的 Markdown

## 快速开始

### 1. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Notion MCP Server 配置
MCP_SERVER_URL=http://localhost:3000/mcp
MCP_AUTH_TOKEN=your-mcp-server-token

# 本服务认证
API_AUTH_TOKEN=your-api-token

# 服务配置
HOST=0.0.0.0
PORT=8000
```

### 4. 启动服务

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API 接口

### 认证

所有请求都需要在 Header 中包含认证信息：

```
Authorization: Bearer your-api-token
```

### 接口列表

#### 1. 获取页面完整内容

```http
GET /api/page/{page_id}
```

返回页面的元数据和 Markdown 格式的内容。

**响应示例：**
```json
{
  "id": "2995ff12-7acc-80b9-bfe6-c77819a09d7c",
  "title": "About Public Wiki",
  "url": "https://www.notion.so/...",
  "created_time": "2025-10-26T06:29:00.000Z",
  "last_edited_time": "2025-10-26T06:30:00.000Z",
  "parent": {
    "type": "database_id",
    "id": "2995ff12-7acc-805a-81d5-e78dbea2221a"
  },
  "properties": {
    "Status": "In progress",
    "Name": "About Public Wiki"
  },
  "content": "# Heading 1\n\nThis is a paragraph.\n\n- List item 1\n- List item 2"
}
```

#### 2. 获取 Database 页面列表

```http
GET /api/database/{database_id}/pages?page_size=100&start_cursor=optional
```

**查询参数：**
- `page_size`: 每页返回的页面数量 (默认: 100)
- `start_cursor`: 分页游标，用于获取下一页

#### 3. 全局搜索

```http
POST /api/search
Content-Type: application/json

{
  "query": "搜索关键词",
  "filter": {"property": "object", "value": "page"},
  "page_size": 10
}
```

**请求体参数：**
- `query`: 搜索关键词
- `filter`: 搜索过滤器 (可选)
- `page_size`: 返回结果数量 (默认: 10)

#### 4. Database 内搜索

```http
POST /api/database/search
Content-Type: application/json

{
  "database_id": "database-id",
  "filter": {...},
  "sorts": [...],
  "page_size": 100
}
```

**请求体参数：**
- `database_id`: 数据库 ID
- `filter`: 过滤条件 (可选)
- `sorts`: 排序条件 (可选)
- `page_size`: 返回结果数量 (默认: 100)
- `start_cursor`: 分页游标 (可选)

#### 5. 健康检查

```http
GET /api/health
```

检查服务状态和 MCP 服务器连接状态。

## 返回格式

### 页面完整内容

```json
{
  "id": "2995ff12-7acc-80b9-bfe6-c77819a09d7c",
  "title": "About Public Wiki",
  "url": "https://www.notion.so/...",
  "created_time": "2025-10-26T06:29:00.000Z",
  "last_edited_time": "2025-10-26T06:30:00.000Z",
  "parent": {
    "type": "database_id",
    "id": "2995ff12-7acc-805a-81d5-e78dbea2221a"
  },
  "properties": {
    "Status": "In progress",
    "Name": "About Public Wiki"
  },
  "content": "# Heading 1\n\nThis is a paragraph.\n\n- List item 1\n- List item 2"
}
```

### 页面列表

```json
{
  "results": [
    {
      "id": "...",
      "title": "mem0",
      "url": "...",
      "properties": {
        "Type": "Research",
        "Tags": ["Design"]
      }
    }
  ],
  "has_more": false,
  "next_cursor": null
}
```

## 使用示例

### 使用 curl 调用 API

```bash
# 1. 获取页面内容
curl -H "Authorization: Bearer your-api-token" \
     http://localhost:8000/api/page/2995ff127acc80b9bfe6c77819a09d7c

# 2. 获取数据库页面列表
curl -H "Authorization: Bearer your-api-token" \
     "http://localhost:8000/api/database/2995ff12-7acc-805a-81d5-e78dbea2221a/pages?page_size=50"

# 3. 全局搜索
curl -X POST -H "Authorization: Bearer your-api-token" \
     -H "Content-Type: application/json" \
     -d '{"query": "About", "page_size": 10}' \
     http://localhost:8000/api/search

# 4. 数据库内搜索
curl -X POST -H "Authorization: Bearer your-api-token" \
     -H "Content-Type: application/json" \
     -d '{"database_id": "2995ff12-7acc-805a-81d5-e78dbea2221a", "page_size": 100}' \
     http://localhost:8000/api/database/search

# 5. 健康检查
curl http://localhost:8000/api/health
```

### 使用 Python requests

```python
import requests

# 配置
API_BASE = "http://localhost:8000"
API_TOKEN = "your-api-token"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# 获取页面内容
page_id = "2995ff12-7acc-80b9-bfe6-c77819a09d7c"
response = requests.get(f"{API_BASE}/api/page/{page_id}", headers=headers)
page_data = response.json()
print(f"页面标题: {page_data['title']}")
print(f"页面内容:\n{page_data['content']}")

# 搜索页面
search_data = {"query": "About", "page_size": 10}
response = requests.post(f"{API_BASE}/api/search", json=search_data, headers=headers)
search_results = response.json()
for page in search_results['results']:
    print(f"- {page['title']}")
```

## 开发

### 项目结构

```
notion-proxy-service/
├── .env.example          # 环境变量示例
├── requirements.txt      # Python 依赖
├── README.md            # 项目说明文档
├── app.py               # FastAPI 主应用
├── client/
│   └── mcp_client.py    # MCP 客户端封装
├── parser/
│   └── notion_parser.py # Notion 数据解析和简化
└── models/
    └── schemas.py       # API 响应模型
```

### 运行开发服务器

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 运行测试套件

```bash
# 确保服务器正在运行，然后执行测试
python test_suite.py
```

测试套件将验证所有 API 端点的功能，包括：
- 服务器健康状态检查
- 认证功能
- 页面内容获取
- 数据库页面列表
- 全局搜索
- 数据库内搜索

### 访问 API 文档

启动服务后，可以访问以下地址查看自动生成的 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 依赖

- FastAPI: REST API 框架
- httpx: 异步 HTTP 客户端
- python-dotenv: 环境变量管理
- pydantic: 数据验证和序列化
- uvicorn: ASGI 服务器
