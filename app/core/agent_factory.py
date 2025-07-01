from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.database import Agent, Tool, AgentTool
from livekit import agents
from livekit.agents import Agent as LiveKitAgent, AgentSession, RoomInputOptions
from livekit.plugins import openai, noise_cancellation
import json


class DynamicAssistant(LiveKitAgent):
    def __init__(self, agent_data: Agent, tools: List[Dict[str, Any]] = None):
        self.agent_data = agent_data
        self.tools = tools or []
        
        # Build instructions with tool information
        instructions = self._build_instructions()
        
        super().__init__(instructions=instructions)
    
    def _build_instructions(self) -> str:
        """Build comprehensive instructions including tool descriptions and knowledge base context"""
        base_instructions = self.agent_data.instructions
        
        # Add knowledge base context
        from app.core.knowledge_service import KnowledgeService
        knowledge_service = KnowledgeService(self.db)
        kb_context = knowledge_service.build_agent_context(self.agent_data.id)
        
        if kb_context:
            base_instructions += f"\n\nKnowledge Base Context:\n{kb_context}"
        
        # Add tool descriptions
        if self.tools:
            tool_instructions = "\n\nAvailable tools:\n"
            for tool in self.tools:
                tool_instructions += f"- {tool['name']}: {tool['description']}\n"
            base_instructions += tool_instructions
        
        return base_instructions


class AgentFactory:
    def __init__(self, db: Session):
        self.db = db
    
    def create_agent_session(self, agent_id: int) -> AgentSession:
        """Create a LiveKit agent session from database agent"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id, Agent.is_active == True).first()
        if not agent:
            raise ValueError(f"Agent with id {agent_id} not found or inactive")
        
        # Get agent tools
        agent_tools = self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent_id,
            AgentTool.is_enabled == True
        ).join(Tool).all()
        
        tools_data = []
        for agent_tool in agent_tools:
            tool_data = {
                'id': agent_tool.tool.id,
                'name': agent_tool.tool.name,
                'description': agent_tool.tool.description,
                'type': agent_tool.tool.tool_type,
                'configuration': agent_tool.configuration or agent_tool.tool.configuration
            }
            tools_data.append(tool_data)
        
        # Create dynamic assistant
        assistant = DynamicAssistant(agent, tools_data)
        
        # Create agent session with configuration
        session = AgentSession(
            llm=openai.realtime.RealtimeModel(
                voice=agent.voice_id,
                temperature=agent.temperature / 10.0,  # Convert 0-10 scale to 0-1
                max_tokens=agent.max_tokens,
                model=agent.model
            )
        )
        
        return session, assistant
    
    def get_agent_configuration(self, agent_id: int) -> Dict[str, Any]:
        """Get agent configuration for API responses"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None
        
        # Get agent tools
        agent_tools = self.db.query(AgentTool).filter(
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
        
        return {
            'agent': agent,
            'tools': tools_data
        }
    
    def validate_agent_tools(self, agent_id: int) -> List[str]:
        """Validate agent tools and return any issues"""
        issues = []
        
        agent_tools = self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent_id,
            AgentTool.is_enabled == True
        ).join(Tool).all()
        
        for agent_tool in agent_tools:
            tool = agent_tool.tool
            
            # Check if tool is active
            if not tool.is_active:
                issues.append(f"Tool '{tool.name}' is inactive")
            
            # Validate tool configuration
            if tool.tool_type == "api" and not tool.configuration.get("endpoint"):
                issues.append(f"API tool '{tool.name}' missing endpoint configuration")
            
            if tool.tool_type == "function" and not tool.configuration.get("function_name"):
                issues.append(f"Function tool '{tool.name}' missing function name")
        
        return issues 