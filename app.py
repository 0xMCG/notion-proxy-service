from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from typing import Optional
import asyncio

from client.mcp_client import MCPClient
from parser.notion_parser import NotionParser
from models.schemas import (
    PageContent, PageListResponse, SearchRequest, DatabaseSearchRequest,
    ErrorResponse
)

load_dotenv()

app = FastAPI(
    title="Notion API 中转服务",
    description="简化的 Notion API 接口，基于 notion-mcp-server",
    version="1.0.0"
)

security = HTTPBearer()

# 认证依赖
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_token = os.getenv("API_AUTH_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=500, detail="API_AUTH_TOKEN not configured")
    
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    return credentials.credentials


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error="Internal server error", detail=str(exc)).dict()
    )


@app.get("/", response_model=dict)
async def root():
    """健康检查端点"""
    return {"message": "Notion API 中转服务运行中", "version": "1.0.0"}


@app.get("/api/page/{page_id}", response_model=PageContent)
async def get_page_content(page_id: str, token: str = Depends(verify_token)):
    """
    获取页面完整内容
    
    - **page_id**: Notion 页面 ID
    - 返回页面的元数据和 Markdown 格式的内容
    """
    async with MCPClient() as mcp_client:
        try:
            page_content = await NotionParser.get_page_content(mcp_client, page_id)
            if not page_content:
                raise HTTPException(status_code=404, detail=f"Page {page_id} not found or failed to retrieve")
            return page_content
        except Exception as e:
            print(f"Error getting page content: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get page content: {str(e)}")


@app.get("/api/database/{database_id}/pages", response_model=PageListResponse)
async def get_database_pages(
    database_id: str,
    page_size: int = 100,
    start_cursor: Optional[str] = None,
    token: str = Depends(verify_token)
):
    """
    获取数据库中的页面列表
    
    - **database_id**: Notion 数据库 ID
    - **page_size**: 每页返回的页面数量 (默认: 100)
    - **start_cursor**: 分页游标，用于获取下一页
    """
    async with MCPClient() as mcp_client:
        try:
            result = await mcp_client.query_database(
                database_id=database_id,
                page_size=page_size,
                start_cursor=start_cursor
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Database not found")
            
            parsed_result = NotionParser.parse_page_list(result)
            return PageListResponse(**parsed_result)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get database pages: {str(e)}")


@app.post("/api/search", response_model=PageListResponse)
async def search_pages(request: SearchRequest, token: str = Depends(verify_token)):
    """
    全局搜索页面
    
    - **query**: 搜索关键词
    - **filter**: 搜索过滤器 (可选)
    - **page_size**: 返回结果数量 (默认: 10)
    """
    async with MCPClient() as mcp_client:
        try:
            result = await mcp_client.search(
                query=request.query,
                filter=request.filter,
                page_size=request.page_size
            )
            
            if not result:
                return PageListResponse(results=[], has_more=False, next_cursor=None)
            
            parsed_result = NotionParser.parse_page_list(result)
            return PageListResponse(**parsed_result)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/database/search", response_model=PageListResponse)
async def search_database_pages(request: DatabaseSearchRequest, token: str = Depends(verify_token)):
    """
    在数据库中搜索页面（支持过滤和排序）
    
    - **database_id**: 数据库 ID
    - **filter**: 过滤条件 (可选)
    - **sorts**: 排序条件 (可选)
    - **page_size**: 返回结果数量 (默认: 100)
    - **start_cursor**: 分页游标 (可选)
    """
    async with MCPClient() as mcp_client:
        try:
            result = await mcp_client.query_database(
                database_id=request.database_id,
                page_size=request.page_size,
                start_cursor=request.start_cursor,
                filter=request.filter,
                sorts=request.sorts
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Database not found")
            
            parsed_result = NotionParser.parse_page_list(result)
            return PageListResponse(**parsed_result)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database search failed: {str(e)}")


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    try:
        # 尝试初始化 MCP 客户端来检查连接
        async with MCPClient() as mcp_client:
            return {
                "status": "healthy",
                "mcp_server_url": os.getenv("MCP_SERVER_URL"),
                "mcp_connected": True
            }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "mcp_server_url": os.getenv("MCP_SERVER_URL"),
                "mcp_connected": False,
                "error": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(app, host=host, port=port)
