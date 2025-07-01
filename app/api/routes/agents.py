from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db, Agent, AgentTool, Tool
from app.schemas.agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentResponse, 
    AgentListResponse,
    AgentWithToolsResponse
)
from app.schemas.tool import AgentToolCreate, AgentToolUpdate, AgentToolResponse
from app.core.agent_factory import AgentFactory

router = APIRouter()


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db)
):
    """Create a new agent"""
    try:
        # Check if agent with same name already exists
        existing_agent = db.query(Agent).filter(Agent.name == agent_data.name).first()
        if existing_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with name '{agent_data.name}' already exists"
            )
        
        # Create new agent
        db_agent = Agent(**agent_data.dict())
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        
        return db_agent
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating agent: {str(e)}"
        )


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    active_only: bool = Query(False, description="Filter only active agents"),
    db: Session = Depends(get_db)
):
    """List all agents with pagination"""
    query = db.query(Agent)
    
    if active_only:
        query = query.filter(Agent.is_active == True)
    
    total = query.count()
    agents = query.offset(skip).limit(limit).all()
    
    return {
        "agents": agents,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit
    }


@router.get("/{agent_id}", response_model=AgentWithToolsResponse)
async def get_agent(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific agent with its tools"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )
    
    # Get agent tools
    agent_tools = db.query(AgentTool).filter(
        AgentTool.agent_id == agent_id
    ).join(Tool).all()
    
    tools_data = []
    for agent_tool in agent_tools:
        tool_data = {
            'id': agent_tool.tool.id,
            'name': agent_tool.tool.name,
            'description': agent_tool.tool.description,
            'type': agent_tool.tool.tool_type,
            'is_enabled': agent_tool.is_enabled,
            'configuration': agent_tool.configuration or agent_tool.tool.configuration
        }
        tools_data.append(tool_data)
    
    # Create response with tools
    response_data = AgentResponse.from_orm(agent).dict()
    response_data['tools'] = tools_data
    
    return response_data


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )
    
    try:
        # Check if name is being changed and if it conflicts
        if agent_data.name and agent_data.name != agent.name:
            existing_agent = db.query(Agent).filter(
                Agent.name == agent_data.name,
                Agent.id != agent_id
            ).first()
            if existing_agent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Agent with name '{agent_data.name}' already exists"
                )
        
        # Update agent fields
        update_data = agent_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)
        
        db.commit()
        db.refresh(agent)
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating agent: {str(e)}"
        )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Delete an agent"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )
    
    try:
        # Check if agent has active calls
        active_calls = db.query(Agent).filter(
            Agent.id == agent_id
        ).join(Agent.calls).filter(
            Agent.calls.any(status__in=["initiated", "connecting", "connected"])
        ).count()
        
        if active_calls > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete agent with active calls. End all calls first."
            )
        
        # Delete agent tools first
        db.query(AgentTool).filter(AgentTool.agent_id == agent_id).delete()
        
        # Delete agent
        db.delete(agent)
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting agent: {str(e)}"
        )


@router.post("/{agent_id}/tools", response_model=AgentToolResponse, status_code=status.HTTP_201_CREATED)
async def add_tool_to_agent(
    agent_id: int,
    tool_data: AgentToolCreate,
    db: Session = Depends(get_db)
):
    """Add a tool to an agent"""
    # Check if agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )
    
    # Check if tool exists
    tool = db.query(Tool).filter(Tool.id == tool_data.tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with id {tool_data.tool_id} not found"
        )
    
    # Check if tool is already assigned to this agent
    existing_assignment = db.query(AgentTool).filter(
        AgentTool.agent_id == agent_id,
        AgentTool.tool_id == tool_data.tool_id
    ).first()
    
    if existing_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{tool.name}' is already assigned to agent '{agent.name}'"
        )
    
    try:
        # Create agent tool assignment
        agent_tool = AgentTool(
            agent_id=agent_id,
            tool_id=tool_data.tool_id,
            is_enabled=tool_data.is_enabled,
            configuration=tool_data.configuration
        )
        db.add(agent_tool)
        db.commit()
        db.refresh(agent_tool)
        
        # Return with tool details
        return {
            "id": agent_tool.id,
            "agent_id": agent_tool.agent_id,
            "tool_id": agent_tool.tool_id,
            "is_enabled": agent_tool.is_enabled,
            "configuration": agent_tool.configuration,
            "created_at": agent_tool.created_at,
            "tool": tool
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding tool to agent: {str(e)}"
        )


@router.put("/{agent_id}/tools/{tool_id}", response_model=AgentToolResponse)
async def update_agent_tool(
    agent_id: int,
    tool_id: int,
    tool_data: AgentToolUpdate,
    db: Session = Depends(get_db)
):
    """Update an agent's tool configuration"""
    agent_tool = db.query(AgentTool).filter(
        AgentTool.agent_id == agent_id,
        AgentTool.tool_id == tool_id
    ).first()
    
    if not agent_tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found for agent {agent_id}"
        )
    
    try:
        # Update tool configuration
        update_data = tool_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent_tool, field, value)
        
        db.commit()
        db.refresh(agent_tool)
        
        # Get tool details
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        
        return {
            "id": agent_tool.id,
            "agent_id": agent_tool.agent_id,
            "tool_id": agent_tool.tool_id,
            "is_enabled": agent_tool.is_enabled,
            "configuration": agent_tool.configuration,
            "created_at": agent_tool.created_at,
            "tool": tool
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating agent tool: {str(e)}"
        )


@router.delete("/{agent_id}/tools/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tool_from_agent(
    agent_id: int,
    tool_id: int,
    db: Session = Depends(get_db)
):
    """Remove a tool from an agent"""
    agent_tool = db.query(AgentTool).filter(
        AgentTool.agent_id == agent_id,
        AgentTool.tool_id == tool_id
    ).first()
    
    if not agent_tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found for agent {agent_id}"
        )
    
    try:
        db.delete(agent_tool)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing tool from agent: {str(e)}"
        )


@router.get("/{agent_id}/tools", response_model=List[AgentToolResponse])
async def get_agent_tools(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get all tools assigned to an agent"""
    # Check if agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )
    
    agent_tools = db.query(AgentTool).filter(
        AgentTool.agent_id == agent_id
    ).join(Tool).all()
    
    return [
        {
            "id": agent_tool.id,
            "agent_id": agent_tool.agent_id,
            "tool_id": agent_tool.tool_id,
            "is_enabled": agent_tool.is_enabled,
            "configuration": agent_tool.configuration,
            "created_at": agent_tool.created_at,
            "tool": agent_tool.tool
        }
        for agent_tool in agent_tools
    ]


@router.post("/{agent_id}/validate", status_code=status.HTTP_200_OK)
async def validate_agent(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Validate an agent's configuration and tools"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found"
        )
    
    try:
        agent_factory = AgentFactory(db)
        issues = agent_factory.validate_agent_tools(agent_id)
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "agent_id": agent_id,
            "agent_name": agent.name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating agent: {str(e)}"
        ) 