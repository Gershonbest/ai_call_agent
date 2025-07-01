from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ToolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tool_type: str = Field(..., min_length=1, max_length=100)
    configuration: Optional[Dict[str, Any]] = None


class ToolCreate(ToolBase):
    pass


class ToolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tool_type: Optional[str] = Field(None, min_length=1, max_length=100)
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ToolResponse(ToolBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentToolCreate(BaseModel):
    tool_id: int
    is_enabled: bool = True
    configuration: Optional[Dict[str, Any]] = None


class AgentToolUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None


class AgentToolResponse(BaseModel):
    id: int
    agent_id: int
    tool_id: int
    is_enabled: bool
    configuration: Optional[Dict[str, Any]] = None
    created_at: datetime
    tool: ToolResponse

    class Config:
        from_attributes = True 