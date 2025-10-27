import httpx
import json
import uuid
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class MCPClient:
    def __init__(self):
        self.server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000/mcp")
        self.auth_token = os.getenv("MCP_AUTH_TOKEN")
        self.session_id = None
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def initialize(self) -> bool:
        """初始化 MCP 会话"""
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-10-26",
                    "capabilities": {},
                    "clientInfo": {"name": "notion-proxy-service", "version": "1.0.0"}
                }
            }
            
            response = await self.client.post(
                self.server_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                # 从响应头中提取 session ID
                session_id_header = response.headers.get("mcp-session-id")
                if session_id_header:
                    self.session_id = session_id_header
                    print(f"Session ID obtained: {self.session_id}")
                    return True
                else:
                    # 如果没有从响应头获取到，生成一个
                    self.session_id = str(uuid.uuid4())
                    print(f"Generated session ID: {self.session_id}")
                    return True
            else:
                print(f"Initialize failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Initialize error: {e}")
            return False
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """调用 MCP 工具"""
        if not self.session_id:
            success = await self.initialize()
            if not success:
                print("Failed to initialize MCP session")
                return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": self.session_id
            }
            
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments
                }
            }
            
            response = await self.client.post(
                self.server_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                # 解析响应
                response_text = response.text
                # print(f"Response text: {response_text[:500]}...")  # 调试用
                
                # 查找 JSON 结果
                lines = response_text.split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # 去掉 'data: ' 前缀
                            if 'result' in data and 'content' in data['result']:
                                content = data['result']['content']
                                if content and len(content) > 0:
                                    # 提取 <json-result> 部分
                                    json_text = content[0].get('text', '')
                                    if '<json-result>' in json_text:
                                        json_start = json_text.find('<json-result>') + len('<json-result>')
                                        json_end = json_text.find('</json-result>')
                                        if json_end > json_start:
                                            json_content = json_text[json_start:json_end]
                                            return json.loads(json_content)
                                    else:
                                        # 如果没有 <json-result> 标签，尝试直接解析
                                        return json.loads(json_text)
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                            continue
                
                # 如果没有找到 data: 行，尝试直接解析整个响应
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    pass
                
                print(f"No valid JSON result found in response: {response_text}")
                return None
            else:
                print(f"Tool call failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Tool call error: {e}")
            return None
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """获取页面信息"""
        return await self.call_tool("API-retrieve-a-page", {"page_id": page_id})
    
    async def get_block_children(self, block_id: str, page_size: int = 100, start_cursor: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取块的子内容"""
        args = {"block_id": block_id, "page_size": page_size}
        if start_cursor:
            args["start_cursor"] = start_cursor
        return await self.call_tool("API-get-block-children", args)
    
    async def search(self, query: str, filter: Optional[Dict[str, Any]] = None, page_size: int = 10) -> Optional[Dict[str, Any]]:
        """全局搜索"""
        args = {"query": query, "page_size": page_size}
        if filter:
            args["filter"] = filter
        return await self.call_tool("API-post-search", args)
    
    async def get_database(self, database_id: str) -> Optional[Dict[str, Any]]:
        """获取数据库信息"""
        return await self.call_tool("API-retrieve-a-database", {"database_id": database_id})
    
    async def query_database(self, database_id: str, page_size: int = 100, start_cursor: Optional[str] = None, 
                           filter: Optional[Dict[str, Any]] = None, sorts: Optional[list] = None) -> Optional[Dict[str, Any]]:
        """查询数据库"""
        args = {"database_id": database_id, "page_size": page_size}
        if start_cursor:
            args["start_cursor"] = start_cursor
        if filter:
            args["filter"] = filter
        if sorts:
            args["sorts"] = sorts
        return await self.call_tool("API-post-database-query", args)
