from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class KnowledgeBaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    kb_type: str = Field(..., min_length=1, max_length=100)


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    kb_type: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    file_path: Optional[str] = Field(None, max_length=500)
    file_type: Optional[str] = Field(None, max_length=50)
    file_size: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    knowledge_base_id: int


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    file_path: Optional[str] = Field(None, max_length=500)
    file_type: Optional[str] = Field(None, max_length=50)
    file_size: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DocumentResponse(DocumentBase):
    id: int
    knowledge_base_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FAQBase(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None


class FAQCreate(FAQBase):
    knowledge_base_id: int


class FAQUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1)
    answer: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class FAQResponse(FAQBase):
    id: int
    knowledge_base_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentKnowledgeBaseCreate(BaseModel):
    knowledge_base_id: int
    is_enabled: bool = True
    priority: int = Field(default=1, ge=1, le=10)


class AgentKnowledgeBaseUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)


class AgentKnowledgeBaseResponse(BaseModel):
    id: int
    agent_id: int
    knowledge_base_id: int
    is_enabled: bool
    priority: int
    created_at: datetime
    knowledge_base: KnowledgeBaseResponse

    class Config:
        from_attributes = True


class KnowledgeBaseWithContent(KnowledgeBaseResponse):
    documents: List[DocumentResponse] = []
    faqs: List[FAQResponse] = []

    class Config:
        from_attributes = True


class KnowledgeBaseListResponse(BaseModel):
    knowledge_bases: List[KnowledgeBaseResponse]
    total: int
    page: int
    per_page: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    per_page: int


class FAQListResponse(BaseModel):
    faqs: List[FAQResponse]
    total: int
    page: int
    per_page: int


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    knowledge_base_ids: Optional[List[int]] = None
    search_type: str = Field(default="all", regex="^(all|documents|faqs)$")
    limit: int = Field(default=10, ge=1, le=50)


class SearchResult(BaseModel):
    type: str  # "document" or "faq"
    id: int
    title: str
    content: str
    knowledge_base_id: int
    knowledge_base_name: str
    relevance_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None 