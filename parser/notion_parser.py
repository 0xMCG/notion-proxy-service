from typing import Dict, Any, List, Optional
from datetime import datetime
from models.schemas import PageInfo, PageContent, ParentInfo


class NotionParser:
    """Notion 数据解析器，将复杂的 Notion API 响应简化为核心字段"""
    
    @staticmethod
    def extract_title_from_properties(properties: Dict[str, Any]) -> str:
        """从 properties 中提取标题"""
        # 查找 title 类型的属性
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title" and prop_data.get("title"):
                title_parts = prop_data["title"]
                if title_parts and len(title_parts) > 0:
                    return title_parts[0].get("plain_text", "")
        
        # 如果没有找到 title，尝试查找 "Name" 属性
        if "Name" in properties:
            name_prop = properties["Name"]
            if name_prop.get("type") == "title" and name_prop.get("title"):
                title_parts = name_prop["title"]
                if title_parts and len(title_parts) > 0:
                    return title_parts[0].get("plain_text", "")
        
        return "Untitled"
    
    @staticmethod
    def simplify_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        """简化 properties，只保留名称和值"""
        simplified = {}
        
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type", "")
            
            if prop_type == "title":
                if prop_data.get("title"):
                    title_parts = prop_data["title"]
                    if title_parts and len(title_parts) > 0:
                        simplified[prop_name] = title_parts[0].get("plain_text", "")
                    else:
                        simplified[prop_name] = ""
                else:
                    simplified[prop_name] = ""
            
            elif prop_type == "rich_text":
                if prop_data.get("rich_text"):
                    text_parts = prop_data["rich_text"]
                    if text_parts and len(text_parts) > 0:
                        simplified[prop_name] = text_parts[0].get("plain_text", "")
                    else:
                        simplified[prop_name] = ""
                else:
                    simplified[prop_name] = ""
            
            elif prop_type == "select":
                if prop_data.get("select"):
                    simplified[prop_name] = prop_data["select"].get("name", "")
                else:
                    simplified[prop_name] = ""
            
            elif prop_type == "multi_select":
                if prop_data.get("multi_select"):
                    values = [item.get("name", "") for item in prop_data["multi_select"]]
                    simplified[prop_name] = values
                else:
                    simplified[prop_name] = []
            
            elif prop_type == "status":
                if prop_data.get("status"):
                    simplified[prop_name] = prop_data["status"].get("name", "")
                else:
                    simplified[prop_name] = ""
            
            elif prop_type == "date":
                if prop_data.get("date"):
                    simplified[prop_name] = prop_data["date"].get("start", "")
                else:
                    simplified[prop_name] = ""
            
            elif prop_type == "people":
                if prop_data.get("people"):
                    names = [person.get("name", "") for person in prop_data["people"]]
                    simplified[prop_name] = names
                else:
                    simplified[prop_name] = []
            
            elif prop_type == "relation":
                if prop_data.get("relation"):
                    simplified[prop_name] = len(prop_data["relation"])
                else:
                    simplified[prop_name] = 0
            
            elif prop_type in ["created_time", "last_edited_time"]:
                simplified[prop_name] = prop_data.get(prop_type, "")
            
            else:
                # 对于其他类型，尝试提取文本内容
                simplified[prop_name] = str(prop_data.get("value", ""))
        
        return simplified
    
    @staticmethod
    def parse_parent(parent_data: Dict[str, Any]) -> Optional[ParentInfo]:
        """解析父节点信息"""
        if not parent_data:
            return None
        
        parent_type = parent_data.get("type", "")
        if parent_type == "database_id":
            return ParentInfo(type="database_id", id=parent_data.get("database_id", ""))
        elif parent_type == "page_id":
            return ParentInfo(type="page_id", id=parent_data.get("page_id", ""))
        
        return None
    
    @staticmethod
    def parse_page(page_data: Dict[str, Any]) -> PageInfo:
        """解析页面数据"""
        properties = page_data.get("properties", {})
        
        return PageInfo(
            id=page_data.get("id", ""),
            title=NotionParser.extract_title_from_properties(properties),
            url=page_data.get("url", ""),
            created_time=datetime.fromisoformat(page_data.get("created_time", "").replace("Z", "+00:00")),
            last_edited_time=datetime.fromisoformat(page_data.get("last_edited_time", "").replace("Z", "+00:00")),
            parent=NotionParser.parse_parent(page_data.get("parent")),
            properties=NotionParser.simplify_properties(properties)
        )
    
    @staticmethod
    def blocks_to_markdown(blocks: List[Dict[str, Any]]) -> str:
        """将 Notion blocks 转换为 Markdown"""
        markdown_lines = []
        
        for block in blocks:
            block_type = block.get("type", "")
            
            if block_type == "paragraph":
                paragraph = block.get("paragraph", {})
                rich_text = paragraph.get("rich_text", [])
                if rich_text:
                    text = "".join([item.get("plain_text", "") for item in rich_text])
                    if text.strip():
                        markdown_lines.append(text)
                    else:
                        markdown_lines.append("")  # 空段落
            
            elif block_type == "heading_1":
                heading = block.get("heading_1", {})
                rich_text = heading.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"# {text}")
            
            elif block_type == "heading_2":
                heading = block.get("heading_2", {})
                rich_text = heading.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"## {text}")
            
            elif block_type == "heading_3":
                heading = block.get("heading_3", {})
                rich_text = heading.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"### {text}")
            
            elif block_type == "bulleted_list_item":
                item = block.get("bulleted_list_item", {})
                rich_text = item.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"- {text}")
            
            elif block_type == "numbered_list_item":
                item = block.get("numbered_list_item", {})
                rich_text = item.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"1. {text}")
            
            elif block_type == "code":
                code_block = block.get("code", {})
                rich_text = code_block.get("rich_text", [])
                language = code_block.get("language", "")
                code_text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"```{language}")
                markdown_lines.append(code_text)
                markdown_lines.append("```")
            
            elif block_type == "quote":
                quote = block.get("quote", {})
                rich_text = quote.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"> {text}")
            
            elif block_type == "divider":
                markdown_lines.append("---")
            
            elif block_type == "to_do":
                todo = block.get("to_do", {})
                rich_text = todo.get("rich_text", [])
                checked = todo.get("checked", False)
                text = "".join([item.get("plain_text", "") for item in rich_text])
                checkbox = "- [x]" if checked else "- [ ]"
                markdown_lines.append(f"{checkbox} {text}")
            
            elif block_type == "toggle":
                toggle = block.get("toggle", {})
                rich_text = toggle.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"<details><summary>{text}</summary>")
                # TODO: 处理 toggle 的子内容
                markdown_lines.append("</details>")
            
            elif block_type == "callout":
                callout = block.get("callout", {})
                rich_text = callout.get("rich_text", [])
                icon = callout.get("icon", {})
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"> **{text}**")
            
            elif block_type == "table":
                # 表格处理比较复杂，暂时跳过
                markdown_lines.append("[Table content not supported yet]")
            
            else:
                # 对于未知类型，尝试提取文本
                if "rich_text" in block:
                    rich_text = block["rich_text"]
                    if rich_text:
                        text = "".join([item.get("plain_text", "") for item in rich_text])
                        if text.strip():
                            markdown_lines.append(text)
        
        return "\n".join(markdown_lines)
    
    @staticmethod
    async def get_page_content(mcp_client, page_id: str) -> Optional[PageContent]:
        """获取页面完整内容（包括 Markdown）"""
        # 获取页面信息
        page_data = await mcp_client.get_page(page_id)
        if not page_data:
            return None
        
        # 解析页面基本信息
        page_info = NotionParser.parse_page(page_data)
        
        # 获取页面内容
        all_blocks = []
        start_cursor = None
        
        while True:
            blocks_data = await mcp_client.get_block_children(page_id, page_size=100, start_cursor=start_cursor)
            if not blocks_data or "results" not in blocks_data:
                break
            
            blocks = blocks_data["results"]
            all_blocks.extend(blocks)
            
            # 检查是否还有更多内容
            if not blocks_data.get("has_more", False):
                break
            
            start_cursor = blocks_data.get("next_cursor")
            if not start_cursor:
                break
        
        # 转换为 Markdown
        markdown_content = NotionParser.blocks_to_markdown(all_blocks)
        
        return PageContent(
            id=page_info.id,
            title=page_info.title,
            url=page_info.url,
            created_time=page_info.created_time,
            last_edited_time=page_info.last_edited_time,
            parent=page_info.parent,
            properties=page_info.properties,
            content=markdown_content
        )
    
    @staticmethod
    def parse_page_list(list_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析页面列表数据"""
        results = []
        
        for item in list_data.get("results", []):
            if item.get("object") == "page":
                page_info = NotionParser.parse_page(item)
                results.append(page_info)
        
        return {
            "results": results,
            "has_more": list_data.get("has_more", False),
            "next_cursor": list_data.get("next_cursor")
        }
