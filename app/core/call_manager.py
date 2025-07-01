import os
import uuid
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from app.models.database import Call, PhoneNumber, Agent
from app.core.agent_factory import AgentFactory
from livekit import agents, rtc, api
from livekit.agents import AgentSession, JobContext, RoomInputOptions, cli, WorkerOptions
from livekit.plugins import openai, noise_cancellation, deepgram, cartesia, silero
from livekit.plugins.turn_detector.english import EnglishModel

logger = logging.getLogger(__name__)


class CallManager:
    def __init__(self, db: Session):
        self.db = db
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
        self.sip_outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
        
        if not all([self.livekit_url, self.livekit_api_key, self.livekit_api_secret]):
            logger.warning("LiveKit credentials not configured. Phone calls will not work.")
        
        if not self.sip_outbound_trunk_id:
            logger.warning("SIP outbound trunk ID not configured. Phone calls will not work.")
    
    async def initiate_call(self, agent_id: int, phone_number: str, caller_number: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Initiate a phone call using LiveKit SIP"""
        try:
            # Validate agent exists and is active
            agent = self.db.query(Agent).filter(Agent.id == agent_id, Agent.is_active == True).first()
            if not agent:
                raise ValueError(f"Agent with id {agent_id} not found or inactive")
            
            # Create or get phone number record
            phone_record = self.db.query(PhoneNumber).filter(
                PhoneNumber.phone_number == phone_number
            ).first()
            
            if not phone_record:
                phone_record = PhoneNumber(
                    phone_number=phone_number,
                    agent_id=agent_id
                )
                self.db.add(phone_record)
                self.db.commit()
                self.db.refresh(phone_record)
            
            # Generate unique room name
            room_name = f"call_{uuid.uuid4().hex}"
            
            # Create call record
            call_record = Call(
                room_name=room_name,
                agent_id=agent_id,
                phone_number_id=phone_record.id,
                caller_number=caller_number,
                status="initiated",
                metadata=metadata or {}
            )
            self.db.add(call_record)
            self.db.commit()
            self.db.refresh(call_record)
            
            # Start the call using LiveKit worker
            await self._start_livekit_call(call_record.id, room_name, agent_id, phone_number, metadata)
            
            return {
                "success": True,
                "call_id": call_record.id,
                "room_name": room_name,
                "status": "initiated"
            }
        
        except Exception as e:
            logger.error(f"Error initiating call: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _start_livekit_call(self, call_id: int, room_name: str, agent_id: int, phone_number: str, metadata: Dict[str, Any] = None):
        """Start a LiveKit call with SIP integration"""
        try:
            # Prepare dial info for the agent
            dial_info = {
                "phone_number": phone_number,
                "transfer_to": metadata.get("transfer_to") if metadata else None,
                "call_id": call_id,
                "agent_id": agent_id
            }
            
            # Create a background task to run the LiveKit worker
            asyncio.create_task(
                self._run_livekit_worker(room_name, agent_id, dial_info)
            )
            
            logger.info(f"Started LiveKit worker for call {call_id} in room {room_name}")
        
        except Exception as e:
            logger.error(f"Error starting LiveKit call: {str(e)}")
            # Update call status to failed
            call_record = self.db.query(Call).filter(Call.id == call_id).first()
            if call_record:
                call_record.status = "failed"
                self.db.commit()
            raise
    
    async def _run_livekit_worker(self, room_name: str, agent_id: int, dial_info: Dict[str, Any]):
        """Run the LiveKit worker for the call"""
        try:
            # Import the worker entrypoint
            from app.workers.call_worker import entrypoint
            
            # Create a mock JobContext for the worker
            # In a real implementation, this would be handled by the LiveKit worker system
            class MockJobContext:
                def __init__(self, room_name: str, dial_info: Dict[str, Any]):
                    self.room = type('Room', (), {'name': room_name})()
                    self.job = type('Job', (), {'metadata': json.dumps(dial_info)})()
                    self.api = None  # Would be set by LiveKit
                
                async def connect(self):
                    pass
                
                async def wait_for_participant(self, identity: str):
                    return type('Participant', (), {'identity': identity})()
                
                def shutdown(self):
                    pass
            
            ctx = MockJobContext(room_name, dial_info)
            
            # Run the worker entrypoint
            await entrypoint(ctx)
            
        except Exception as e:
            logger.error(f"Error in LiveKit worker: {str(e)}")
            # Update call status to failed
            call_record = self.db.query(Call).filter(Call.room_name == room_name).first()
            if call_record:
                call_record.status = "failed"
                self.db.commit()
    
    async def end_call(self, call_id: int) -> Dict[str, Any]:
        """End an active call"""
        try:
            call_record = self.db.query(Call).filter(Call.id == call_id).first()
            if not call_record:
                raise ValueError(f"Call with id {call_id} not found")
            
            # Update call status
            call_record.status = "completed"
            self.db.commit()
            
            return {
                "success": True,
                "message": "Call ended successfully"
            }
        
        except Exception as e:
            logger.error(f"Error ending call: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_call_status(self, call_id: int) -> Optional[Dict[str, Any]]:
        """Get the status of a call"""
        call_record = self.db.query(Call).filter(Call.id == call_id).first()
        if not call_record:
            return None
        
        return {
            "id": call_record.id,
            "call_sid": call_record.call_sid,
            "room_name": call_record.room_name,
            "status": call_record.status,
            "duration": call_record.duration,
            "created_at": call_record.created_at.isoformat(),
            "updated_at": call_record.updated_at.isoformat() if call_record.updated_at else None
        }
    
    def list_calls(self, agent_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List calls with optional filtering"""
        query = self.db.query(Call)
        
        if agent_id:
            query = query.filter(Call.agent_id == agent_id)
        
        if status:
            query = query.filter(Call.status == status)
        
        total = query.count()
        calls = query.order_by(Call.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "calls": [self.get_call_status(call.id) for call in calls],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def update_call_status(self, room_name: str, status: str, duration: Optional[int] = None, recording_url: Optional[str] = None):
        """Update call status from LiveKit events"""
        call_record = self.db.query(Call).filter(Call.room_name == room_name).first()
        if not call_record:
            logger.warning(f"Call with room {room_name} not found")
            return
        
        call_record.status = status
        if duration:
            call_record.duration = duration
        if recording_url:
            call_record.recording_url = recording_url
        
        self.db.commit()
        logger.info(f"Updated call {call_record.id} status to {status}") 