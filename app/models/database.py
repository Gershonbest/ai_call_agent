from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./voice_agent.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    instructions = Column(Text, nullable=False)
    voice_id = Column(String(100), default="coral")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Agent configuration
    temperature = Column(Integer, default=7)  # 0-10 scale
    max_tokens = Column(Integer, default=1000)
    model = Column(String(100), default="gpt-4")
    
    # Relationships
    tools = relationship("AgentTool", back_populates="agent")
    calls = relationship("Call", back_populates="agent")
    phone_numbers = relationship("PhoneNumber", back_populates="agent")
    knowledge_bases = relationship("AgentKnowledgeBase", back_populates="agent")


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    tool_type = Column(String(100), nullable=False)  # function, api, webhook, etc.
    configuration = Column(JSON)  # Store tool-specific configuration
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    agent_tools = relationship("AgentTool", back_populates="tool")


class AgentTool(Base):
    __tablename__ = "agent_tools"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)
    is_enabled = Column(Boolean, default=True)
    configuration = Column(JSON)  # Override tool configuration for this agent
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="tools")
    tool = relationship("Tool", back_populates="agent_tools")


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, unique=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="phone_numbers")
    calls = relationship("Call", back_populates="phone_number")


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    call_sid = Column(String(255), unique=True)  # Twilio call SID
    room_name = Column(String(255), unique=True)  # LiveKit room name
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    phone_number_id = Column(Integer, ForeignKey("phone_numbers.id"))
    caller_number = Column(String(20))
    status = Column(String(50), default="initiated")  # initiated, connected, completed, failed
    duration = Column(Integer)  # in seconds
    recording_url = Column(String(500))
    transcript = Column(Text)
    call_metadata = Column(JSON)  # Additional call metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="calls")
    phone_number = relationship("PhoneNumber", back_populates="calls")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    kb_type = Column(String(100), nullable=False)  # document, faq, custom, vector
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="knowledge_base")
    faqs = relationship("FAQ", back_populates="knowledge_base")
    agent_kbs = relationship("AgentKnowledgeBase", back_populates="knowledge_base")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_path = Column(String(500))  # For uploaded files
    file_type = Column(String(50))  # pdf, docx, txt, etc.
    file_size = Column(Integer)  # in bytes
    document_metadata = Column(JSON)  # Additional document metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100))
    tags = Column(JSON)  # Array of tags
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="faqs")


class AgentKnowledgeBase(Base):
    __tablename__ = "agent_knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    is_enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Higher number = higher priority
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="knowledge_bases")
    knowledge_base = relationship("KnowledgeBase", back_populates="agent_kbs")


# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 