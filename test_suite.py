#!/usr/bin/env python3
"""
Notion API 中转服务测试套件

测试所有 API 端点的功能
"""
import asyncio
import json
import os
import sys
import time
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class NotionAPITester:
    """Notion API 测试器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_token = os.getenv("API_AUTH_TOKEN", "your-api-token")
        self.headers = {"Authorization": f"Bearer {self.api_token}"}
        
        # 测试数据
        self.test_page_id = "2385ff127acc80889b3fe39ba7f5e209"
        self.test_database_id = "2995ff127acc805a81d5e78dbea2221a"
    
    def test_server_health(self) -> bool:
        """测试服务器健康状态"""
        print("🔍 Testing server health...")
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server is healthy:")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   MCP Server URL: {data.get('mcp_server_url', 'unknown')}")
                print(f"   MCP Connected: {data.get('mcp_connected', False)}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_root_endpoint(self) -> bool:
        """测试根端点"""
        print("\n🔍 Testing root endpoint...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint: {data}")
                return True
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            return False
    
    def test_get_page_content(self) -> bool:
        """测试获取页面内容"""
        print(f"\n🔍 Testing get page content (ID: {self.test_page_id})...")
        try:
            response = requests.get(
                f"{self.base_url}/api/page/{self.test_page_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Page content retrieved:")
                print(f"   Title: {data.get('title', 'No title')}")
                print(f"   URL: {data.get('url', 'No URL')}")
                print(f"   Created: {data.get('created_time', 'Unknown')}")
                print(f"   Last edited: {data.get('last_edited_time', 'Unknown')}")
                print(f"   Content length: {len(data.get('content', ''))} characters")
                
                # 显示内容预览
                content = data.get('content', '')
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"   Content preview: {preview}")
                
                # 显示属性
                properties = data.get('properties', {})
                if properties:
                    print(f"   Properties ({len(properties)}):")
                    for key, value in list(properties.items())[:5]:  # 显示前5个属性
                        if isinstance(value, list):
                            value_str = f"[{', '.join(map(str, value))}]"
                        else:
                            value_str = str(value)
                        print(f"     - {key}: {value_str}")
                    if len(properties) > 5:
                        print(f"     ... and {len(properties) - 5} more properties")
                
                # 显示父节点信息
                parent = data.get('parent')
                if parent:
                    print(f"   Parent: {parent.get('type', 'unknown')} - {parent.get('id', 'unknown')}")
                
                return True
            else:
                print(f"❌ Get page content failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Get page content error: {e}")
            return False
    
    def test_get_database_pages(self) -> bool:
        """测试获取数据库页面列表"""
        print(f"\n🔍 Testing get database pages (ID: {self.test_database_id})...")
        try:
            response = requests.get(
                f"{self.base_url}/api/database/{self.test_database_id}/pages",
                headers=self.headers,
                params={"page_size": 50},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ Database pages retrieved:")
                print(f"   Total pages: {len(results)}")
                print(f"   Has more: {data.get('has_more', False)}")
                print(f"   Next cursor: {data.get('next_cursor', 'None')}")
                
                # 显示每个页面的详细信息
                for i, page in enumerate(results):
                    print(f"   Page {i+1}:")
                    print(f"     Title: {page.get('title', 'No title')}")
                    print(f"     URL: {page.get('url', 'No URL')}")
                    print(f"     ID: {page.get('id', 'No ID')}")
                    print(f"     Created: {page.get('created_time', 'Unknown')}")
                    print(f"     Last edited: {page.get('last_edited_time', 'Unknown')}")
                    
                    # 显示主要属性
                    properties = page.get('properties', {})
                    if properties:
                        main_props = []
                        for key, value in properties.items():
                            if isinstance(value, list) and value:
                                main_props.append(f"{key}: [{', '.join(map(str, value))}]")
                            elif value and str(value).strip():
                                main_props.append(f"{key}: {value}")
                        
                        if main_props:
                            print(f"     Properties: {', '.join(main_props[:3])}")  # 显示前3个属性
                    
                    print()  # 空行分隔
                
                return True
            else:
                print(f"❌ Get database pages failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Get database pages error: {e}")
            return False
    
    def test_global_search(self) -> bool:
        """测试全局搜索"""
        print("\n🔍 Testing global search...")
        try:
            search_data = {
                "query": "About",
                "filter": {"property": "object", "value": "page"},
                "page_size": 5
            }
            
            response = requests.post(
                f"{self.base_url}/api/search",
                headers=self.headers,
                json=search_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ Global search completed:")
                print(f"   Query: '{search_data['query']}'")
                print(f"   Filter: {search_data['filter']}")
                print(f"   Results found: {len(results)}")
                print(f"   Has more: {data.get('has_more', False)}")
                
                # 显示搜索结果详情
                for i, page in enumerate(results):
                    print(f"   Result {i+1}:")
                    print(f"     Title: {page.get('title', 'No title')}")
                    print(f"     URL: {page.get('url', 'No URL')}")
                    print(f"     ID: {page.get('id', 'No ID')}")
                    
                    # 显示匹配的属性
                    properties = page.get('properties', {})
                    if properties:
                        main_props = []
                        for key, value in properties.items():
                            if isinstance(value, list) and value:
                                main_props.append(f"{key}: [{', '.join(map(str, value))}]")
                            elif value and str(value).strip():
                                main_props.append(f"{key}: {value}")
                        
                        if main_props:
                            print(f"     Properties: {', '.join(main_props[:2])}")  # 显示前2个属性
                    
                    print()  # 空行分隔
                
                return True
            else:
                print(f"❌ Global search failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Global search error: {e}")
            return False
    
    def test_database_search(self) -> bool:
        """测试数据库内搜索"""
        print(f"\n🔍 Testing database search (ID: {self.test_database_id})...")
        try:
            search_data = {
                "database_id": self.test_database_id,
                "page_size": 5
            }
            
            response = requests.post(
                f"{self.base_url}/api/database/search",
                headers=self.headers,
                json=search_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ Database search completed:")
                print(f"   Database ID: {self.test_database_id}")
                print(f"   Results found: {len(results)}")
                print(f"   Has more: {data.get('has_more', False)}")
                
                # 显示搜索结果详情
                for i, page in enumerate(results):
                    print(f"   Result {i+1}:")
                    print(f"     Title: {page.get('title', 'No title')}")
                    print(f"     URL: {page.get('url', 'No URL')}")
                    print(f"     ID: {page.get('id', 'No ID')}")
                    print(f"     Created: {page.get('created_time', 'Unknown')}")
                    
                    # 显示主要属性
                    properties = page.get('properties', {})
                    if properties:
                        main_props = []
                        for key, value in properties.items():
                            if isinstance(value, list) and value:
                                main_props.append(f"{key}: [{', '.join(map(str, value))}]")
                            elif value and str(value).strip():
                                main_props.append(f"{key}: {value}")
                        
                        if main_props:
                            print(f"     Properties: {', '.join(main_props[:3])}")  # 显示前3个属性
                    
                    print()  # 空行分隔
                
                return True
            else:
                print(f"❌ Database search failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Database search error: {e}")
            return False
    
    def test_authentication(self) -> bool:
        """测试认证功能"""
        print("\n🔍 Testing authentication...")
        try:
            # 测试无效 token
            invalid_headers = {"Authorization": "Bearer invalid-token"}
            response = requests.get(
                f"{self.base_url}/api/page/{self.test_page_id}",
                headers=invalid_headers,
                timeout=30
            )
            
            if response.status_code == 401:
                print("✅ Authentication correctly rejects invalid token")
                
                # 测试有效 token
                response = requests.get(
                    f"{self.base_url}/api/page/{self.test_page_id}",
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print("✅ Authentication accepts valid token")
                    return True
                else:
                    print(f"❌ Valid token rejected: {response.status_code}")
                    return False
            else:
                print(f"❌ Authentication test failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication test error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🚀 Starting Notion API 中转服务测试套件")
        print("=" * 60)
        
        tests = {
            "Server Health": self.test_server_health,
            "Root Endpoint": self.test_root_endpoint,
            "Authentication": self.test_authentication,
            "Get Page Content": self.test_get_page_content,
            "Get Database Pages": self.test_get_database_pages,
            "Global Search": self.test_global_search,
            "Database Search": self.test_database_search,
        }
        
        results = {}
        start_time = time.time()
        
        for test_name, test_func in tests.items():
            try:
                test_start = time.time()
                results[test_name] = test_func()
                test_duration = time.time() - test_start
                print(f"⏱️  {test_name} completed in {test_duration:.2f}s")
            except Exception as e:
                print(f"❌ {test_name} test crashed: {e}")
                results[test_name] = False
        
        total_duration = time.time() - start_time
        
        # 打印测试结果摘要
        print("\n" + "=" * 60)
        print("📊 测试结果摘要:")
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        print(f"\n📈 测试统计:")
        print(f"   总测试数: {total}")
        print(f"   通过: {passed}")
        print(f"   失败: {total - passed}")
        print(f"   成功率: {(passed/total)*100:.1f}%")
        print(f"   总耗时: {total_duration:.2f}s")
        
        if passed == total:
            print("\n🎉 所有测试通过！API 服务运行正常。")
        else:
            print(f"\n⚠️  {total - passed} 个测试失败，请检查配置和服务器状态。")
        
        return results


def main():
    """主函数"""
    print("Notion API 中转服务测试套件")
    print("确保服务器正在运行: uvicorn app:app --host 0.0.0.0 --port 8000")
    print()
    
    tester = NotionAPITester()
    results = tester.run_all_tests()
    
    # 如果有测试失败，退出码为1
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
