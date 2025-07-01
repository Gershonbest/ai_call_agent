from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db, Call, Agent, PhoneNumber
from app.schemas.call import (
    CallCreate, CallUpdate, CallResponse, CallListResponse, CallInitiateRequest
)
from app.core.call_manager import CallManager

router = APIRouter()


@router.post("/initiate", status_code=status.HTTP_201_CREATED)
async def initiate_call(
    call_data: CallInitiateRequest,
    db: Session = Depends(get_db)
):
    """Initiate a new outbound call using LiveKit SIP"""
    call_manager = CallManager(db)
    result = await call_manager.initiate_call(
        agent_id=call_data.agent_id,
        phone_number=call_data.phone_number,
        caller_number=call_data.caller_number,
        metadata=call_data.metadata
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result


@router.get("/", response_model=CallListResponse)
async def list_calls(
    agent_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all calls with optional filtering"""
    call_manager = CallManager(db)
    result = call_manager.list_calls(
        agent_id=agent_id,
        status=status_filter,
        limit=limit,
        offset=skip
    )
    return result


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: int,
    db: Session = Depends(get_db)
):
    """Get details of a specific call"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with id {call_id} not found"
        )
    return call


@router.put("/{call_id}", response_model=CallResponse)
async def update_call(
    call_id: int,
    call_data: CallUpdate,
    db: Session = Depends(get_db)
):
    """Update a call's status, duration, or recording URL"""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Call with id {call_id} not found"
        )
    update_data = call_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(call, field, value)
    db.commit()
    db.refresh(call)
    return call


@router.post("/{call_id}/end", status_code=status.HTTP_200_OK)
async def end_call(
    call_id: int,
    db: Session = Depends(get_db)
):
    """End an active call"""
    call_manager = CallManager(db)
    result = await call_manager.end_call(call_id)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    return result 