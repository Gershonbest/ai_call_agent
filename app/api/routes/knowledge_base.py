from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.models.database import get_db, KnowledgeBase, Document, FAQ, AgentKnowledgeBase, Agent
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse, KnowledgeBaseWithContent,
    DocumentCreate, DocumentUpdate, DocumentResponse,
    FAQCreate, FAQUpdate, FAQResponse,
    AgentKnowledgeBaseCreate, AgentKnowledgeBaseUpdate, AgentKnowledgeBaseResponse,
    KnowledgeBaseListResponse, DocumentListResponse, FAQListResponse,
    SearchRequest, SearchResult
)
from app.core.knowledge_service import KnowledgeService

router = APIRouter()


# Knowledge Base Management
@router.post("/", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db)
):
    """Create a new knowledge base"""
    try:
        # Check if knowledge base with same name already exists
        existing_kb = db.query(KnowledgeBase).filter(KnowledgeBase.name == kb_data.name).first()
        if existing_kb:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Knowledge base with name '{kb_data.name}' already exists"
            )
        
        # Validate knowledge base type
        valid_types = ["document", "faq", "custom", "vector"]
        if kb_data.kb_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid knowledge base type. Must be one of: {valid_types}"
            )
        
        # Create new knowledge base
        db_kb = KnowledgeBase(**kb_data.dict())
        db.add(db_kb)
        db.commit()
        db.refresh(db_kb)
        
        return db_kb
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating knowledge base: {str(e)}"
        )


@router.get("/", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(False),
    kb_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all knowledge bases with pagination and filtering"""
    query = db.query(KnowledgeBase)
    
    if active_only:
        query = query.filter(KnowledgeBase.is_active == True)
    
    if kb_type:
        query = query.filter(KnowledgeBase.kb_type == kb_type)
    
    total = query.count()
    knowledge_bases = query.offset(skip).limit(limit).all()
    
    return {
        "knowledge_bases": knowledge_bases,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit
    }


@router.get("/{kb_id}", response_model=KnowledgeBaseWithContent)
async def get_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific knowledge base with its content"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base with id {kb_id} not found"
        )
    
    # Get documents and FAQs
    documents = db.query(Document).filter(
        Document.knowledge_base_id == kb_id,
        Document.is_active == True
    ).all()
    
    faqs = db.query(FAQ).filter(
        FAQ.knowledge_base_id == kb_id,
        FAQ.is_active == True
    ).all()
    
    # Create response with content
    response_data = KnowledgeBaseResponse.from_orm(kb).dict()
    response_data['documents'] = documents
    response_data['faqs'] = faqs
    
    return response_data


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_data: KnowledgeBaseUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing knowledge base"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base with id {kb_id} not found"
        )
    
    try:
        # Check if name is being changed and if it conflicts
        if kb_data.name and kb_data.name != kb.name:
            existing_kb = db.query(KnowledgeBase).filter(
                KnowledgeBase.name == kb_data.name,
                KnowledgeBase.id != kb_id
            ).first()
            if existing_kb:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Knowledge base with name '{kb_data.name}' already exists"
                )
        
        # Update knowledge base fields
        update_data = kb_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(kb, field, value)
        
        db.commit()
        db.refresh(kb)
        
        return kb
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating knowledge base: {str(e)}"
        )


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """Delete a knowledge base"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base with id {kb_id} not found"
        )
    
    try:
        # Check if knowledge base is assigned to any agents
        agent_assignments = db.query(AgentKnowledgeBase).filter(
            AgentKnowledgeBase.knowledge_base_id == kb_id
        ).count()
        
        if agent_assignments > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete knowledge base '{kb.name}' - it is assigned to {agent_assignments} agent(s). Remove from agents first."
            )
        
        # Delete knowledge base (cascade will handle documents and FAQs)
        db.delete(kb)
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting knowledge base: {str(e)}"
        )


# Document Management
@router.post("/{kb_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    kb_id: int,
    document_data: DocumentCreate,
    db: Session = Depends(get_db)
):
    """Create a new document in a knowledge base"""
    # Check if knowledge base exists
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base with id {kb_id} not found"
        )
    
    try:
        # Create document
        doc_data = document_data.dict()
        doc_data['knowledge_base_id'] = kb_id
        db_doc = Document(**doc_data)
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        
        return db_doc
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating document: {str(e)}"
        )


@router.post("/{kb_id}/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    title: str = Query(..., description="Document title"),
    db: Session = Depends(get_db)
):
    """Upload a document file to a knowledge base"""
    # Check if knowledge base exists
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base with id {kb_id} not found"
        )
    
    # Validate file type
    allowed_types = ["txt", "pdf", "docx", "md"]
    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {allowed_types}"
        )
    
    try:
        # Read file content
        content = await file.read()
        content_text = content.decode('utf-8') if file_extension == "txt" else str(content)
        
        # Save file to storage (in production, use cloud storage)
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create document record
        db_doc = Document(
            knowledge_base_id=kb_id,
            title=title,
            content=content_text,
            file_path=file_path,
            file_type=file_extension,
            file_size=len(content),
            metadata={"original_filename": file.filename}
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        
        return db_doc
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/{kb_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    kb_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all documents in a knowledge base"""
    # Check if knowledge base exists
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base with id {kb_id} not found"
        )
    
    documents = db.query(Document).filter(
        Document.knowledge_base_id == kb_id,
        Document.is_active == True
    ).offset(skip).limit(limit).all()
    
    total = db.query(Document).filter(
        Document.knowledge_base_id == kb_id,
        Document.is_active == True
    ).count()
    
    return {
        "documents": documents,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit
    }


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific document"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {doc_id} not found"
        )
    return doc


@router.put("/documents/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: int,
    document_data: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """Update a document"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {doc_id} not found"
        )
    
    update_data = document_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)
    
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {doc_id} not found"
        )
    
    try:
        # Delete file if it exists
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        
        db.delete(doc)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


# FAQ Management
@router.post("/{kb_id}/faqs", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
async def create_faq(
    kb_id: int,
    faq_data: FAQCreate,
    db: Session = Depends(get_db)
):
    """Create a new FAQ in a knowledge base"""
    # Check if knowledge base exists
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base with id {kb_id} not found"
        )
    
    try:
        # Create FAQ
        faq_dict = faq_data.dict()
        faq_dict['knowledge_base_id'] = kb_id
        db_faq = FAQ(**faq_dict)
        db.add(db_faq)
        db.commit()
        db.refresh(db_faq)
        
        return db_faq
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating FAQ: {str(e)}"
        )


@router.get("/{kb_id}/faqs", response_model=FAQListResponse)
async def list_faqs(
    kb_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all FAQs in a knowledge base"""
    # Check if knowledge base exists
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base with id {kb_id} not found"
        )
    
    query = db.query(FAQ).filter(
        FAQ.knowledge_base_id == kb_id,
        FAQ.is_active == True
    )
    
    if category:
        query = query.filter(FAQ.category == category)
    
    faqs = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "faqs": faqs,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit
    }


@router.get("/faqs/{faq_id}", response_model=FAQResponse)
async def get_faq(
    faq_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific FAQ"""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAQ with id {faq_id} not found"
        )
    return faq


@router.put("/faqs/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: int,
    faq_data: FAQUpdate,
    db: Session = Depends(get_db)
):
    """Update a FAQ"""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAQ with id {faq_id} not found"
        )
    
    update_data = faq_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(faq, field, value)
    
    db.commit()
    db.refresh(faq)
    return faq


@router.delete("/faqs/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db)
):
    """Delete a FAQ"""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FAQ with id {faq_id} not found"
        )
    
    try:
        db.delete(faq)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting FAQ: {str(e)}"
        )


# Agent Knowledge Base Assignment
@router.post("/agents/{agent_id}/knowledge-bases", response_model=AgentKnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def assign_knowledge_base_to_agent(
    agent_id: int,
    kb_data: AgentKnowledgeBaseCreate,
    db: Session = Depends(get_db)
):
    """Assign a knowledge base to an agent"""
    # Check if agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )
    
    # Check if knowledge base exists
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_data.knowledge_base_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base with id {kb_data.knowledge_base_id} not found"
        )
    
    # Check if already assigned
    existing = db.query(AgentKnowledgeBase).filter(
        AgentKnowledgeBase.agent_id == agent_id,
        AgentKnowledgeBase.knowledge_base_id == kb_data.knowledge_base_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Knowledge base '{kb.name}' is already assigned to agent '{agent.name}'"
        )
    
    try:
        # Create assignment
        agent_kb = AgentKnowledgeBase(
            agent_id=agent_id,
            knowledge_base_id=kb_data.knowledge_base_id,
            is_enabled=kb_data.is_enabled,
            priority=kb_data.priority
        )
        db.add(agent_kb)
        db.commit()
        db.refresh(agent_kb)
        
        # Return with knowledge base details
        return {
            "id": agent_kb.id,
            "agent_id": agent_kb.agent_id,
            "knowledge_base_id": agent_kb.knowledge_base_id,
            "is_enabled": agent_kb.is_enabled,
            "priority": agent_kb.priority,
            "created_at": agent_kb.created_at,
            "knowledge_base": kb
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning knowledge base to agent: {str(e)}"
        )


@router.get("/agents/{agent_id}/knowledge-bases", response_model=List[AgentKnowledgeBaseResponse])
async def get_agent_knowledge_bases(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get all knowledge bases assigned to an agent"""
    # Check if agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )
    
    agent_kbs = db.query(AgentKnowledgeBase).filter(
        AgentKnowledgeBase.agent_id == agent_id
    ).join(KnowledgeBase).all()
    
    return [
        {
            "id": agent_kb.id,
            "agent_id": agent_kb.agent_id,
            "knowledge_base_id": agent_kb.knowledge_base_id,
            "is_enabled": agent_kb.is_enabled,
            "priority": agent_kb.priority,
            "created_at": agent_kb.created_at,
            "knowledge_base": agent_kb.knowledge_base
        }
        for agent_kb in agent_kbs
    ]


@router.delete("/agents/{agent_id}/knowledge-bases/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_knowledge_base_from_agent(
    agent_id: int,
    kb_id: int,
    db: Session = Depends(get_db)
):
    """Remove a knowledge base from an agent"""
    agent_kb = db.query(AgentKnowledgeBase).filter(
        AgentKnowledgeBase.agent_id == agent_id,
        AgentKnowledgeBase.knowledge_base_id == kb_id
    ).first()
    
    if not agent_kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base {kb_id} not found for agent {agent_id}"
        )
    
    try:
        db.delete(agent_kb)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing knowledge base from agent: {str(e)}"
        )


# Search functionality
@router.post("/search", response_model=List[SearchResult])
async def search_knowledge_bases(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Search through knowledge bases"""
    knowledge_service = KnowledgeService(db)
    results = knowledge_service.search_knowledge_base(search_request)
    return results


@router.get("/types/available", status_code=status.HTTP_200_OK)
async def get_available_knowledge_base_types():
    """Get available knowledge base types and their descriptions"""
    return {
        "types": [
            {
                "name": "document",
                "description": "Store and search through documents and files",
                "features": ["File upload", "Text extraction", "Document search"]
            },
            {
                "name": "faq",
                "description": "Store frequently asked questions and answers",
                "features": ["Q&A pairs", "Categorization", "Tagging"]
            },
            {
                "name": "custom",
                "description": "Custom knowledge base for specific use cases",
                "features": ["Flexible structure", "Custom fields", "API integration"]
            },
            {
                "name": "vector",
                "description": "Vector-based knowledge base for semantic search",
                "features": ["Embeddings", "Semantic search", "AI-powered retrieval"]
            }
        ]
    } 