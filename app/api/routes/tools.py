from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db, Tool, AgentTool
from app.schemas.tool import ToolCreate, ToolUpdate, ToolResponse
from app.core.tool_executor import FunctionRegistry

router = APIRouter()


@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    db: Session = Depends(get_db)
):
    """Create a new tool"""
    try:
        # Check if tool with same name already exists
        existing_tool = db.query(Tool).filter(Tool.name == tool_data.name).first()
        if existing_tool:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tool with name '{tool_data.name}' already exists"
            )
        
        # Validate tool type
        valid_types = ["api", "function", "webhook"]
        if tool_data.tool_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tool type. Must be one of: {valid_types}"
            )
        
        # Validate configuration based on tool type
        if tool_data.configuration:
            if tool_data.tool_type == "api" and "endpoint" not in tool_data.configuration:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API tools must have an 'endpoint' in configuration"
                )
            elif tool_data.tool_type == "function" and "function_name" not in tool_data.configuration:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Function tools must have a 'function_name' in configuration"
                )
            elif tool_data.tool_type == "webhook" and "webhook_url" not in tool_data.configuration:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Webhook tools must have a 'webhook_url' in configuration"
                )
        
        # Create new tool
        db_tool = Tool(**tool_data.dict())
        db.add(db_tool)
        db.commit()
        db.refresh(db_tool)
        
        return db_tool
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tool: {str(e)}"
        )


@router.get("/", response_model=List[ToolResponse])
async def list_tools(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    active_only: bool = Query(False, description="Filter only active tools"),
    tool_type: Optional[str] = Query(None, description="Filter by tool type"),
    db: Session = Depends(get_db)
):
    """List all tools with pagination and filtering"""
    query = db.query(Tool)
    
    if active_only:
        query = query.filter(Tool.is_active == True)
    
    if tool_type:
        query = query.filter(Tool.tool_type == tool_type)
    
    tools = query.offset(skip).limit(limit).all()
    
    return tools


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific tool"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with id {tool_id} not found"
        )
    
    return tool


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    tool_data: ToolUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing tool"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with id {tool_id} not found"
        )
    
    try:
        # Check if name is being changed and if it conflicts
        if tool_data.name and tool_data.name != tool.name:
            existing_tool = db.query(Tool).filter(
                Tool.name == tool_data.name,
                Tool.id != tool_id
            ).first()
            if existing_tool:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tool with name '{tool_data.name}' already exists"
                )
        
        # Validate tool type if being changed
        if tool_data.tool_type and tool_data.tool_type != tool.tool_type:
            valid_types = ["api", "function", "webhook"]
            if tool_data.tool_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid tool type. Must be one of: {valid_types}"
                )
        
        # Validate configuration if provided
        if tool_data.configuration:
            tool_type = tool_data.tool_type or tool.tool_type
            if tool_type == "api" and "endpoint" not in tool_data.configuration:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="API tools must have an 'endpoint' in configuration"
                )
            elif tool_type == "function" and "function_name" not in tool_data.configuration:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Function tools must have a 'function_name' in configuration"
                )
            elif tool_type == "webhook" and "webhook_url" not in tool_data.configuration:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Webhook tools must have a 'webhook_url' in configuration"
                )
        
        # Update tool fields
        update_data = tool_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tool, field, value)
        
        db.commit()
        db.refresh(tool)
        
        return tool
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tool: {str(e)}"
        )


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: int,
    db: Session = Depends(get_db)
):
    """Delete a tool"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with id {tool_id} not found"
        )
    
    try:
        # Check if tool is assigned to any agents
        agent_assignments = db.query(AgentTool).filter(AgentTool.tool_id == tool_id).count()
        if agent_assignments > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete tool '{tool.name}' - it is assigned to {agent_assignments} agent(s). Remove from agents first."
            )
        
        # Delete tool
        db.delete(tool)
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tool: {str(e)}"
        )


@router.get("/types/available", status_code=status.HTTP_200_OK)
async def get_available_tool_types():
    """Get available tool types and their requirements"""
    return {
        "types": [
            {
                "name": "api",
                "description": "HTTP API calls to external services",
                "required_config": ["endpoint"],
                "optional_config": ["method", "headers", "auth", "default_params"]
            },
            {
                "name": "function",
                "description": "Internal function calls",
                "required_config": ["function_name"],
                "optional_config": ["parameters"]
            },
            {
                "name": "webhook",
                "description": "Webhook calls to external services",
                "required_config": ["webhook_url"],
                "optional_config": ["method", "headers", "default_payload"]
            }
        ]
    }


@router.get("/functions/available", status_code=status.HTTP_200_OK)
async def get_available_functions():
    """Get list of available functions for function tools"""
    function_registry = FunctionRegistry()
    functions = function_registry.list_functions()
    
    return {
        "functions": functions,
        "total": len(functions)
    }


@router.post("/{tool_id}/test", status_code=status.HTTP_200_OK)
async def test_tool(
    tool_id: int,
    parameters: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Test a tool with given parameters"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with id {tool_id} not found"
        )
    
    if not tool.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot test inactive tool"
        )
    
    try:
        from app.core.tool_executor import ToolExecutor
        executor = ToolExecutor()
        
        tool_config = {
            "name": tool.name,
            "type": tool.tool_type,
            "configuration": tool.configuration or {}
        }
        
        result = await executor.execute_tool(tool_config, parameters)
        await executor.close()
        
        return {
            "tool_id": tool_id,
            "tool_name": tool.name,
            "test_result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing tool: {str(e)}"
        )


@router.get("/{tool_id}/agents", status_code=status.HTTP_200_OK)
async def get_tool_agents(
    tool_id: int,
    db: Session = Depends(get_db)
):
    """Get all agents that use this tool"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool with id {tool_id} not found"
        )
    
    agent_tools = db.query(AgentTool).filter(
        AgentTool.tool_id == tool_id
    ).join(AgentTool.agent).all()
    
    agents = []
    for agent_tool in agent_tools:
        agent_data = {
            "id": agent_tool.agent.id,
            "name": agent_tool.agent.name,
            "is_active": agent_tool.agent.is_active,
            "tool_enabled": agent_tool.is_enabled,
            "tool_configuration": agent_tool.configuration
        }
        agents.append(agent_data)
    
    return {
        "tool_id": tool_id,
        "tool_name": tool.name,
        "agents": agents,
        "total": len(agents)
    } 