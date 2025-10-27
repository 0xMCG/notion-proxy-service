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
    async def get_block_children_content(mcp_client, block_id: str) -> str:
        """递归获取块的子内容"""
        all_child_blocks = []
        start_cursor = None
        
        while True:
            child_blocks_data = await mcp_client.get_block_children(block_id, page_size=100, start_cursor=start_cursor)
            if not child_blocks_data or "results" not in child_blocks_data:
                break
            
            child_blocks = child_blocks_data["results"]
            all_child_blocks.extend(child_blocks)
            
            # 检查是否还有更多内容
            if not child_blocks_data.get("has_more", False):
                break
            
            start_cursor = child_blocks_data.get("next_cursor")
            if not start_cursor:
                break
        
        # 递归转换为 Markdown
        return await NotionParser.blocks_to_markdown(all_child_blocks, mcp_client)
    
    @staticmethod
    async def get_table_content(mcp_client, table_id: str, table_width: int, has_column_header: bool, has_row_header: bool) -> str:
        """获取表格内容并转换为 Markdown 表格"""
        all_table_rows = []
        start_cursor = None
        
        while True:
            table_rows_data = await mcp_client.get_block_children(table_id, page_size=100, start_cursor=start_cursor)
            if not table_rows_data or "results" not in table_rows_data:
                break
            
            table_rows = table_rows_data["results"]
            all_table_rows.extend(table_rows)
            
            # 检查是否还有更多内容
            if not table_rows_data.get("has_more", False):
                break
            
            start_cursor = table_rows_data.get("next_cursor")
            if not start_cursor:
                break
        
        if not all_table_rows:
            return ""
        
        # 处理表格行
        markdown_rows = []
        for i, row in enumerate(all_table_rows):
            if row.get("type") == "table_row":
                cells = row.get("table_row", {}).get("cells", [])
                row_content = []
                
                for cell in cells:
                    # 提取单元格内容
                    cell_text = ""
                    for text_item in cell:
                        if text_item.get("type") == "text":
                            cell_text += text_item.get("plain_text", "")
                    
                    # 清理单元格内容，替换换行符
                    cell_text = cell_text.replace("\n", " ").strip()
                    row_content.append(cell_text)
                
                # 确保行有足够的列
                while len(row_content) < table_width:
                    row_content.append("")
                
                markdown_rows.append("| " + " | ".join(row_content) + " |")
                
                # 添加表头分隔线
                if i == 0 and has_column_header:
                    separator = "| " + " | ".join(["---"] * table_width) + " |"
                    markdown_rows.insert(-1, separator)
        
        return "\n".join(markdown_rows)
    
    @staticmethod
    async def blocks_to_markdown(blocks: List[Dict[str, Any]], mcp_client=None) -> str:
        """将 Notion blocks 转换为 Markdown"""
        markdown_lines = []
        
        for block in blocks:
            block_type = block.get("type", "")
            block_id = block.get("id", "")
            has_children = block.get("has_children", False)
            
            if block_type == "paragraph":
                paragraph = block.get("paragraph", {})
                rich_text = paragraph.get("rich_text", [])
                if rich_text:
                    text = "".join([item.get("plain_text", "") for item in rich_text])
                    if text.strip():
                        markdown_lines.append(text)
                    else:
                        markdown_lines.append("")  # 空段落
                else:
                    markdown_lines.append("")  # 空段落
                
                # 处理段落的子内容
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
            
            elif block_type == "heading_1":
                heading = block.get("heading_1", {})
                rich_text = heading.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"# {text}")
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
            
            elif block_type == "heading_2":
                heading = block.get("heading_2", {})
                rich_text = heading.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"## {text}")
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
            
            elif block_type == "heading_3":
                heading = block.get("heading_3", {})
                rich_text = heading.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"### {text}")
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
            
            elif block_type == "bulleted_list_item":
                item = block.get("bulleted_list_item", {})
                rich_text = item.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"- {text}")
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        # 为子内容添加缩进
                        indented_content = "\n".join([f"  {line}" for line in child_content.split("\n")])
                        markdown_lines.append(indented_content)
            
            elif block_type == "numbered_list_item":
                item = block.get("numbered_list_item", {})
                rich_text = item.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"1. {text}")
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        # 为子内容添加缩进
                        indented_content = "\n".join([f"  {line}" for line in child_content.split("\n")])
                        markdown_lines.append(indented_content)
            
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
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        # 为子内容添加引用格式
                        quoted_content = "\n".join([f"> {line}" for line in child_content.split("\n")])
                        markdown_lines.append(quoted_content)
            
            elif block_type == "divider":
                markdown_lines.append("---")
            
            elif block_type == "to_do":
                todo = block.get("to_do", {})
                rich_text = todo.get("rich_text", [])
                checked = todo.get("checked", False)
                text = "".join([item.get("plain_text", "") for item in rich_text])
                checkbox = "- [x]" if checked else "- [ ]"
                markdown_lines.append(f"{checkbox} {text}")
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        # 为子内容添加缩进
                        indented_content = "\n".join([f"  {line}" for line in child_content.split("\n")])
                        markdown_lines.append(indented_content)
            
            elif block_type == "toggle":
                toggle = block.get("toggle", {})
                rich_text = toggle.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"**{text}**")
                
                # 处理 toggle 的子内容
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
            
            elif block_type == "callout":
                callout = block.get("callout", {})
                rich_text = callout.get("rich_text", [])
                icon = callout.get("icon", {})
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"> **{text}**")
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        # 为子内容添加引用格式
                        quoted_content = "\n".join([f"> {line}" for line in child_content.split("\n")])
                        markdown_lines.append(quoted_content)
            
            elif block_type == "table":
                # 处理表格
                table = block.get("table", {})
                table_width = table.get("table_width", 0)
                has_column_header = table.get("has_column_header", False)
                has_row_header = table.get("has_row_header", False)
                
                # 获取表格的子内容（表格行）
                if has_children and mcp_client:
                    table_content = await NotionParser.get_table_content(mcp_client, block_id, table_width, has_column_header, has_row_header)
                    if table_content:
                        markdown_lines.append(table_content)
                else:
                    markdown_lines.append("[Empty table]")
            
            elif block_type == "table_row":
                # 表格行会在 get_table_content 中处理
                pass
            
            elif block_type == "image":
                image = block.get("image", {})
                if image.get("type") == "external":
                    url = image.get("external", {}).get("url", "")
                    caption = image.get("caption", [])
                    caption_text = "".join([item.get("plain_text", "") for item in caption])
                    if caption_text:
                        markdown_lines.append(f"![{caption_text}]({url})")
                    else:
                        markdown_lines.append(f"![]({url})")
                else:
                    markdown_lines.append("[Image content not supported]")
            
            elif block_type == "video":
                video = block.get("video", {})
                if video.get("type") == "external":
                    url = video.get("external", {}).get("url", "")
                    caption = video.get("caption", [])
                    caption_text = "".join([item.get("plain_text", "") for item in caption])
                    if caption_text:
                        markdown_lines.append(f"[{caption_text}]({url})")
                    else:
                        markdown_lines.append(f"[Video]({url})")
                else:
                    markdown_lines.append("[Video content not supported]")
            
            elif block_type == "file":
                file_block = block.get("file", {})
                if file_block.get("type") == "external":
                    url = file_block.get("external", {}).get("url", "")
                    caption = file_block.get("caption", [])
                    caption_text = "".join([item.get("plain_text", "") for item in caption])
                    if caption_text:
                        markdown_lines.append(f"[{caption_text}]({url})")
                    else:
                        markdown_lines.append(f"[File]({url})")
                else:
                    markdown_lines.append("[File content not supported]")
            
            elif block_type == "pdf":
                pdf = block.get("pdf", {})
                if pdf.get("type") == "external":
                    url = pdf.get("external", {}).get("url", "")
                    caption = pdf.get("caption", [])
                    caption_text = "".join([item.get("plain_text", "") for item in caption])
                    if caption_text:
                        markdown_lines.append(f"[{caption_text}]({url})")
                    else:
                        markdown_lines.append(f"[PDF]({url})")
                else:
                    markdown_lines.append("[PDF content not supported]")
            
            elif block_type == "bookmark":
                bookmark = block.get("bookmark", {})
                url = bookmark.get("url", "")
                caption = bookmark.get("caption", [])
                caption_text = "".join([item.get("plain_text", "") for item in caption])
                if caption_text:
                    markdown_lines.append(f"[{caption_text}]({url})")
                else:
                    markdown_lines.append(f"[Bookmark]({url})")
            
            elif block_type == "embed":
                embed = block.get("embed", {})
                url = embed.get("url", "")
                markdown_lines.append(f"[Embedded content]({url})")
            
            elif block_type == "equation":
                equation = block.get("equation", {})
                expression = equation.get("expression", "")
                markdown_lines.append(f"$${expression}$$")
            
            elif block_type == "synced_block":
                synced_block = block.get("synced_block", {})
                synced_from = synced_block.get("synced_from")
                if synced_from:
                    markdown_lines.append("[Synced block - content from another page]")
                else:
                    markdown_lines.append("[Synced block]")
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
            
            elif block_type == "template":
                template = block.get("template", {})
                rich_text = template.get("rich_text", [])
                text = "".join([item.get("plain_text", "") for item in rich_text])
                markdown_lines.append(f"**Template: {text}**")
                
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
            
            elif block_type == "link_to_page":
                link_to_page = block.get("link_to_page", {})
                if link_to_page.get("type") == "page_id":
                    page_id = link_to_page.get("page_id", "")
                    markdown_lines.append(f"[Link to page]({page_id})")
                elif link_to_page.get("type") == "database_id":
                    database_id = link_to_page.get("database_id", "")
                    markdown_lines.append(f"[Link to database]({database_id})")
                else:
                    markdown_lines.append("[Link to page]")
            
            elif block_type == "child_page":
                child_page = block.get("child_page", {})
                title = child_page.get("title", "Untitled")
                markdown_lines.append(f"**Child Page: {title}**")
            
            elif block_type == "child_database":
                child_database = block.get("child_database", {})
                title = child_database.get("title", "Untitled Database")
                markdown_lines.append(f"**Child Database: {title}**")
            
            elif block_type == "column_list":
                # 列列表容器
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
            
            elif block_type == "column":
                # 列容器
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
            
            else:
                # 对于未知类型，尝试提取文本
                if "rich_text" in block:
                    rich_text = block["rich_text"]
                    if rich_text:
                        text = "".join([item.get("plain_text", "") for item in rich_text])
                        if text.strip():
                            markdown_lines.append(text)
                
                # 处理未知类型的子内容
                if has_children and mcp_client:
                    child_content = await NotionParser.get_block_children_content(mcp_client, block_id)
                    if child_content:
                        markdown_lines.append(child_content)
        
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
        
        # 转换为 Markdown（支持递归获取子内容）
        markdown_content = await NotionParser.blocks_to_markdown(all_blocks, mcp_client)
        
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
