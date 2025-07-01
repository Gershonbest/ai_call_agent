from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: str = Field(..., min_length=1)
    voice_id: str = Field(default="coral", max_length=100)
    temperature: int = Field(default=7, ge=0, le=10)
    max_tokens: int = Field(default=1000, ge=1)
    model: str = Field(default="gpt-4", max_length=100)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = Field(None, min_length=1)
    voice_id: Optional[str] = Field(None, max_length=100)
    temperature: Optional[int] = Field(None, ge=0, le=10)
    max_tokens: Optional[int] = Field(None, ge=1)
    model: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
    page: int
    per_page: int


class AgentWithToolsResponse(AgentResponse):
    tools: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True 