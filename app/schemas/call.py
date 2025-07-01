from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class CallBase(BaseModel):
    agent_id: int
    phone_number_id: Optional[int] = None
    caller_number: Optional[str] = Field(None, max_length=20)
    metadata: Optional[Dict[str, Any]] = None


class CallCreate(CallBase):
    pass


class CallUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=50)
    duration: Optional[int] = Field(None, ge=0)
    recording_url: Optional[str] = Field(None, max_length=500)
    transcript: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CallResponse(CallBase):
    id: int
    call_sid: Optional[str] = None
    room_name: Optional[str] = None
    status: str
    duration: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CallListResponse(BaseModel):
    calls: list[CallResponse]
    total: int
    page: int
    per_page: int


class PhoneNumberBase(BaseModel):
    phone_number: str = Field(..., max_length=20)
    agent_id: Optional[int] = None


class PhoneNumberCreate(PhoneNumberBase):
    pass


class PhoneNumberUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, max_length=20)
    agent_id: Optional[int] = None
    is_active: Optional[bool] = None


class PhoneNumberResponse(PhoneNumberBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CallInitiateRequest(BaseModel):
    agent_id: int
    phone_number: str = Field(..., max_length=20)
    caller_number: Optional[str] = Field(None, max_length=20)
    metadata: Optional[Dict[str, Any]] = None 