# Notion Proxy Service API 文档

## 概述

Notion Proxy Service 是一个基于 FastAPI 的 REST API 服务，作为 Notion MCP Server 的中转层，提供简化的 Notion 内容访问接口。该服务支持获取页面内容、数据库页面列表、全局搜索和数据库搜索等功能，并将 Notion 内容转换为人类可读的 Markdown 格式。

## 基础信息

- **服务地址**: `http://localhost:8000`
- **认证方式**: Bearer Token
- **响应格式**: JSON
- **字符编码**: UTF-8

## 认证

所有 API 请求都需要在请求头中包含有效的认证令牌：

```http
Authorization: Bearer your-api-token
```

## 通用响应格式

### 成功响应
```json
{
  "id": "string",
  "title": "string", 
  "url": "string",
  "created_time": "2025-01-01T00:00:00Z",
  "last_edited_time": "2025-01-01T00:00:00Z",
  "parent": {
    "type": "database_id|page_id|workspace",
    "id": "string"
  },
  "properties": {
    "key": "value"
  },
  "content": "string"
}
```

### 错误响应
```json
{
  "detail": "错误描述信息"
}
```

## API 接口

### 1. 健康检查

检查服务运行状态。

**请求**
```http
GET /api/health
```

**响应**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

### 2. 获取页面内容

获取指定页面的完整内容，包括所有子内容（支持递归获取）。

**请求**
```http
GET /api/page/{page_id}
```

**路径参数**
- `page_id` (string, 必需): Notion 页面 ID

**请求头**
```http
Authorization: Bearer your-api-token
```

**响应示例**
```json
{
  "id": "23e5ff12-7acc-80de-9e15-cd58adfde504",
  "title": "AI Agent 2025年上半年汇总",
  "url": "https://www.notion.so/AI-Agent-2025-23e5ff127acc80de9e15-cd58adfde504",
  "created_time": "2025-07-28T01:35:00Z",
  "last_edited_time": "2025-10-27T12:25:00Z",
  "parent": {
    "type": "database_id",
    "id": "2995ff12-7acc-805a-81d5-e78dbea2221a"
  },
  "properties": {
    "Parent page": 0,
    "Date": "",
    "Sub-page": 0,
    "Last edited time": "2025-10-27T12:25:00.000Z",
    "Tags": [],
    "Type": "Knowledge",
    "Page": "AI Agent 2025年上半年汇总",
    "Verification": "",
    "Owner": ["Sam"]
  },
  "content": "**（手工基于公开信息进行汇总）2025年上半年零散的新闻搜集**\n\n## 2025-07-25\n### Claude Code推出subagents功能\n智能体可以调用其他子智能体，通过多个智能体协作完成任务。\n官方文档：https://docs.anthropic.com/en/docs/claude-code/sub-agents\n\n## 2025-07-28\n### 微软发布GitHub Spark\n全栈编程工具，通过对话即可生成完整应用，前后端齐全。39美元/月的付费用户可用。\n官方介绍：https://github.com/features/spark\n\n..."
}
```

**内容格式说明**
- `content` 字段包含完整的 Markdown 格式内容
- 支持所有 Notion 块类型，包括：
  - 标题（H1、H2、H3）
  - 段落文本
  - 列表（有序、无序）
  - 代码块
  - 引用
  - 分隔线
  - 待办事项
  - **折叠内容（Toggle）**：显示为加粗文本，包含完整子内容
  - 提示框（Callout）
  - 表格（Markdown 格式）
  - 图片、视频、文件等媒体内容
  - 数学公式（LaTeX）
  - 同步块、模板
  - 页面链接
  - 列布局容器

### 3. 获取数据库页面列表

获取指定数据库中的所有页面。

**请求**
```http
GET /api/database/{database_id}/pages
```

**路径参数**
- `database_id` (string, 必需): Notion 数据库 ID

**查询参数**
- `page_size` (integer, 可选): 每页返回的页面数量，默认 10，最大 100
- `start_cursor` (string, 可选): 分页游标，用于获取下一页

**请求头**
```http
Authorization: Bearer your-api-token
```

**响应示例**
```json
{
  "pages": [
    {
      "id": "23e5ff12-7acc-80de-9e15-cd58adfde504",
      "title": "AI Agent 2025年上半年汇总",
      "url": "https://www.notion.so/AI-Agent-2025-23e5ff127acc80de9e15-cd58adfde504",
      "created_time": "2025-07-28T01:35:00Z",
      "last_edited_time": "2025-10-27T12:25:00Z",
      "properties": {
        "Type": "Knowledge",
        "Owner": ["Sam"],
        "Tags": []
      }
    }
  ],
  "has_more": false,
  "next_cursor": null
}
```

### 4. 全局搜索

在整个工作区中搜索内容。

**请求**
```http
POST /api/search
```

**请求头**
```http
Authorization: Bearer your-api-token
Content-Type: application/json
```

**请求体**
```json
{
  "query": "AI Agent",
  "page_size": 10
}
```

**请求体参数**
- `query` (string, 必需): 搜索关键词
- `page_size` (integer, 可选): 每页返回的结果数量，默认 10，最大 100

**响应示例**
```json
{
  "results": [
    {
      "id": "23e5ff12-7acc-80de-9e15-cd58adfde504",
      "title": "AI Agent 2025年上半年汇总",
      "url": "https://www.notion.so/AI-Agent-2025-23e5ff127acc80de9e15-cd58adfde504",
      "created_time": "2025-07-28T01:35:00Z",
      "properties": {
        "Type": "Knowledge",
        "Owner": ["Sam"]
      }
    }
  ],
  "has_more": false,
  "next_cursor": null
}
```

### 5. 数据库搜索

在指定数据库中搜索内容。

**请求**
```http
POST /api/database/search
```

**请求头**
```http
Authorization: Bearer your-api-token
Content-Type: application/json
```

**请求体**
```json
{
  "database_id": "2995ff12-7acc-805a-81d5-e78dbea2221a",
  "query": "AI Agent",
  "page_size": 10
}
```

**请求体参数**
- `database_id` (string, 必需): Notion 数据库 ID
- `query` (string, 必需): 搜索关键词
- `page_size` (integer, 可选): 每页返回的结果数量，默认 10，最大 100

**响应示例**
```json
{
  "results": [
    {
      "id": "23e5ff12-7acc-80de-9e15-cd58adfde504",
      "title": "AI Agent 2025年上半年汇总",
      "url": "https://www.notion.so/AI-Agent-2025-23e5ff127acc80de9e15-cd58adfde504",
      "created_time": "2025-07-28T01:35:00Z",
      "properties": {
        "Type": "Knowledge",
        "Owner": ["Sam"]
      }
    }
  ],
  "has_more": false,
  "next_cursor": null
}
```

## 错误码

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 使用示例

### cURL 示例

**获取页面内容**
```bash
curl -H "Authorization: Bearer your-api-token" \
     http://localhost:8000/api/page/23e5ff127acc80de9e15cd58adfde504
```

**获取数据库页面列表**
```bash
curl -H "Authorization: Bearer your-api-token" \
     "http://localhost:8000/api/database/2995ff127acc805a81d5e78dbea2221a/pages?page_size=20"
```

**全局搜索**
```bash
curl -X POST \
     -H "Authorization: Bearer your-api-token" \
     -H "Content-Type: application/json" \
     -d '{"query": "AI Agent", "page_size": 10}' \
     http://localhost:8000/api/search
```

**数据库搜索**
```bash
curl -X POST \
     -H "Authorization: Bearer your-api-token" \
     -H "Content-Type: application/json" \
     -d '{"database_id": "2995ff127acc805a81d5e78dbea2221a", "query": "AI Agent", "page_size": 10}' \
     http://localhost:8000/api/database/search
```

### Python requests 示例

```python
import requests

# 配置
base_url = "http://localhost:8000"
headers = {"Authorization": "Bearer your-api-token"}

# 获取页面内容
page_id = "23e5ff127acc80de9e15cd58adfde504"
response = requests.get(f"{base_url}/api/page/{page_id}", headers=headers)
page_content = response.json()
print(f"页面标题: {page_content['title']}")
print(f"内容长度: {len(page_content['content'])} 字符")

# 获取数据库页面列表
database_id = "2995ff127acc805a81d5e78dbea2221a"
response = requests.get(f"{base_url}/api/database/{database_id}/pages", headers=headers)
pages = response.json()
print(f"找到 {len(pages['pages'])} 个页面")

# 全局搜索
search_data = {"query": "AI Agent", "page_size": 10}
response = requests.post(f"{base_url}/api/search", headers=headers, json=search_data)
results = response.json()
print(f"搜索结果: {len(results['results'])} 个")

# 数据库搜索
db_search_data = {
    "database_id": database_id,
    "query": "AI Agent", 
    "page_size": 10
}
response = requests.post(f"{base_url}/api/database/search", headers=headers, json=db_search_data)
db_results = response.json()
print(f"数据库搜索结果: {len(db_results['results'])} 个")
```

### JavaScript fetch 示例

```javascript
const baseUrl = 'http://localhost:8000';
const headers = {
  'Authorization': 'Bearer your-api-token',
  'Content-Type': 'application/json'
};

// 获取页面内容
async function getPageContent(pageId) {
  const response = await fetch(`${baseUrl}/api/page/${pageId}`, { headers });
  const data = await response.json();
  console.log(`页面标题: ${data.title}`);
  console.log(`内容长度: ${data.content.length} 字符`);
  return data;
}

// 获取数据库页面列表
async function getDatabasePages(databaseId, pageSize = 10) {
  const response = await fetch(`${baseUrl}/api/database/${databaseId}/pages?page_size=${pageSize}`, { headers });
  const data = await response.json();
  console.log(`找到 ${data.pages.length} 个页面`);
  return data;
}

// 全局搜索
async function searchContent(query, pageSize = 10) {
  const response = await fetch(`${baseUrl}/api/search`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ query, page_size: pageSize })
  });
  const data = await response.json();
  console.log(`搜索结果: ${data.results.length} 个`);
  return data;
}

// 数据库搜索
async function searchDatabase(databaseId, query, pageSize = 10) {
  const response = await fetch(`${baseUrl}/api/database/search`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ database_id: databaseId, query, page_size: pageSize })
  });
  const data = await response.json();
  console.log(`数据库搜索结果: ${data.results.length} 个`);
  return data;
}

// 使用示例
const pageId = '23e5ff127acc80de9e15cd58adfde504';
const databaseId = '2995ff127acc805a81d5e78dbea2221a';

getPageContent(pageId);
getDatabasePages(databaseId);
searchContent('AI Agent');
searchDatabase(databaseId, 'AI Agent');
```