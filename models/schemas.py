from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union
from datetime import datetime


class ParentInfo(BaseModel):
    type: str  # "database_id" or "page_id"
    id: str


class PageInfo(BaseModel):
    id: str
    title: str
    url: str
    created_time: datetime
    last_edited_time: datetime
    parent: Optional[ParentInfo] = None
    properties: Dict[str, Any] = {}


class PageContent(PageInfo):
    content: str  # Markdown content


class SearchRequest(BaseModel):
    query: str
    filter: Optional[Dict[str, Any]] = None
    page_size: int = 10


class DatabaseSearchRequest(BaseModel):
    database_id: str
    filter: Optional[Dict[str, Any]] = None
    sorts: Optional[List[Dict[str, Any]]] = None
    page_size: int = 100
    start_cursor: Optional[str] = None


class PageListResponse(BaseModel):
    results: List[PageInfo]
    has_more: bool
    next_cursor: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
