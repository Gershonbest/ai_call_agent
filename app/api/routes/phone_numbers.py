from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db, PhoneNumber, Agent
from app.schemas.call import PhoneNumberCreate, PhoneNumberUpdate, PhoneNumberResponse

router = APIRouter()


@router.post("/", response_model=PhoneNumberResponse, status_code=status.HTTP_201_CREATED)
async def create_phone_number(
    phone_data: PhoneNumberCreate,
    db: Session = Depends(get_db)
):
    """Create a new phone number and optionally assign to an agent"""
    try:
        # Check if phone number already exists
        existing = db.query(PhoneNumber).filter(PhoneNumber.phone_number == phone_data.phone_number).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Phone number '{phone_data.phone_number}' already exists"
            )
        
        # Optionally check agent exists
        if phone_data.agent_id:
            agent = db.query(Agent).filter(Agent.id == phone_data.agent_id).first()
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent with id {phone_data.agent_id} not found"
                )
        
        db_phone = PhoneNumber(**phone_data.dict())
        db.add(db_phone)
        db.commit()
        db.refresh(db_phone)
        return db_phone
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating phone number: {str(e)}"
        )


@router.get("/", response_model=List[PhoneNumberResponse])
async def list_phone_numbers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    agent_id: Optional[int] = Query(None),
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List all phone numbers with optional filtering"""
    query = db.query(PhoneNumber)
    if agent_id:
        query = query.filter(PhoneNumber.agent_id == agent_id)
    if active_only:
        query = query.filter(PhoneNumber.is_active == True)
    numbers = query.offset(skip).limit(limit).all()
    return numbers


@router.get("/{phone_id}", response_model=PhoneNumberResponse)
async def get_phone_number(
    phone_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific phone number"""
    phone = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number with id {phone_id} not found"
        )
    return phone


@router.put("/{phone_id}", response_model=PhoneNumberResponse)
async def update_phone_number(
    phone_id: int,
    phone_data: PhoneNumberUpdate,
    db: Session = Depends(get_db)
):
    """Update a phone number or reassign to an agent"""
    phone = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number with id {phone_id} not found"
        )
    if phone_data.agent_id:
        agent = db.query(Agent).filter(Agent.id == phone_data.agent_id).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {phone_data.agent_id} not found"
            )
    update_data = phone_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(phone, field, value)
    db.commit()
    db.refresh(phone)
    return phone


@router.delete("/{phone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_phone_number(
    phone_id: int,
    db: Session = Depends(get_db)
):
    """Delete a phone number"""
    phone = db.query(PhoneNumber).filter(PhoneNumber.id == phone_id).first()
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone number with id {phone_id} not found"
        )
    try:
        db.delete(phone)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting phone number: {str(e)}"
        ) 