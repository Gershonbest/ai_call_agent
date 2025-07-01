from __future__ import annotations

import asyncio
import logging
import json
import os
from typing import Any, Dict
from dotenv import load_dotenv

from livekit import rtc, api
from livekit.agents import (
    AgentSession,
    Agent,
    JobContext,
    function_tool,
    RunContext,
    get_job_context,
    cli,
    WorkerOptions,
    RoomInputOptions,
)
from livekit.plugins import (
    deepgram,
    openai,
    cartesia,
    silero,
    noise_cancellation,
)
from livekit.plugins.turn_detector.english import EnglishModel

# Load environment variables
load_dotenv()
logger = logging.getLogger("voice-agent-worker")
logger.setLevel(logging.INFO)

# Get SIP trunk configuration
sip_outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
if not sip_outbound_trunk_id:
    logger.error("SIP_OUTBOUND_TRUNK_ID not configured")
    raise ValueError("SIP_OUTBOUND_TRUNK_ID environment variable is required")


class DynamicVoiceAgent(Agent):
    def __init__(
        self,
        *,
        agent_config: Dict[str, Any],
        dial_info: Dict[str, Any],
    ):
        # Build instructions with tool information
        instructions = self._build_instructions(agent_config, dial_info)
        
        super().__init__(instructions=instructions)
        
        # Store configuration
        self.agent_config = agent_config
        self.dial_info = dial_info
        self.participant: rtc.RemoteParticipant | None = None

    def _build_instructions(self, agent_config: Dict[str, Any], dial_info: Dict[str, Any]) -> str:
        """Build comprehensive instructions including tool descriptions"""
        base_instructions = agent_config.get("instructions", "You are a helpful voice AI assistant.")
        
        # Add tool descriptions if available
        tools = agent_config.get("tools", [])
        if tools:
            tool_instructions = "\n\nAvailable tools:\n"
            for tool in tools:
                tool_instructions += f"- {tool['name']}: {tool['description']}\n"
            base_instructions += tool_instructions
        
        # Add context from dial_info
        if dial_info.get("context"):
            base_instructions += f"\n\nContext: {dial_info['context']}"
        
        return base_instructions

    def set_participant(self, participant: rtc.RemoteParticipant):
        self.participant = participant

    async def hangup(self):
        """Helper function to hang up the call by deleting the room"""
        job_ctx = get_job_context()
        try:
            await job_ctx.api.room.delete_room(
                api.DeleteRoomRequest(
                    room=job_ctx.room.name,
                )
            )
        except Exception as e:
            logger.error(f"Error hanging up call: {e}")

    @function_tool()
    async def transfer_call(self, ctx: RunContext):
        """Transfer the call to a human agent, called after confirming with the user"""
        transfer_to = self.dial_info.get("transfer_to")
        if not transfer_to:
            return "Cannot transfer call - no transfer number configured"

        logger.info(f"Transferring call to {transfer_to}")

        # Let the message play fully before transferring
        await ctx.session.generate_reply(
            instructions="Let the user know you'll be transferring them to a human agent."
        )

        job_ctx = get_job_context()
        try:
            await job_ctx.api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=job_ctx.room.name,
                    participant_identity=self.participant.identity,
                    transfer_to=f"tel:{transfer_to}",
                )
            )
            logger.info(f"Transferred call to {transfer_to}")
            return "Call transferred successfully"
        except Exception as e:
            logger.error(f"Error transferring call: {e}")
            await ctx.session.generate_reply(
                instructions="There was an error transferring the call."
            )
            await self.hangup()
            return f"Transfer failed: {str(e)}"

    @function_tool()
    async def end_call(self, ctx: RunContext):
        """Called when the user wants to end the call"""
        logger.info(f"Ending the call for {self.participant.identity}")

        # Let the agent finish speaking
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()

        await self.hangup()
        return "Call ended"

    @function_tool()
    async def detected_answering_machine(self, ctx: RunContext):
        """Called when the call reaches voicemail. Use this tool AFTER you hear the voicemail greeting"""
        logger.info(f"Detected answering machine for {self.participant.identity}")
        await self.hangup()
        return "Call ended due to answering machine"

    # Dynamic tool execution based on agent configuration
    async def execute_dynamic_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Any:
        """Execute a tool based on the agent's configuration"""
        tools = self.agent_config.get("tools", [])
        tool_config = next((t for t in tools if t["name"] == tool_name), None)
        
        if not tool_config:
            return f"Tool '{tool_name}' not found"
        
        try:
            # Import tool executor
            from app.core.tool_executor import ToolExecutor
            executor = ToolExecutor()
            
            result = await executor.execute_tool(tool_config, parameters)
            await executor.close()
            
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Error executing tool: {str(e)}"


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the LiveKit worker"""
    logger.info(f"Connecting to room {ctx.room.name}")
    await ctx.connect()

    # Parse dial info from job metadata
    dial_info = json.loads(ctx.job.metadata)
    phone_number = dial_info["phone_number"]
    agent_id = dial_info["agent_id"]
    call_id = dial_info["call_id"]

    # Get agent configuration from database
    from app.models.database import SessionLocal, Agent, AgentTool, Tool
    
    db = SessionLocal()
    try:
        agent_record = db.query(Agent).filter(Agent.id == agent_id, Agent.is_active == True).first()
        if not agent_record:
            raise ValueError(f"Agent with id {agent_id} not found or inactive")
        
        # Get agent tools
        agent_tools = db.query(AgentTool).filter(
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
        
        # Build agent configuration
        agent_config = {
            "id": agent_record.id,
            "name": agent_record.name,
            "description": agent_record.description,
            "instructions": agent_record.instructions,
            "voice_id": agent_record.voice_id,
            "temperature": agent_record.temperature,
            "max_tokens": agent_record.max_tokens,
            "model": agent_record.model,
            "tools": tools_data
        }
        
    finally:
        db.close()

    # Create the dynamic agent
    agent = DynamicVoiceAgent(
        agent_config=agent_config,
        dial_info=dial_info,
    )

    # Create agent session with configuration
    session = AgentSession(
        turn_detection=EnglishModel(),
        vad=silero.VAD.load(),
        llm=openai.realtime.RealtimeModel(
            voice=agent_record.voice_id,
            temperature=agent_record.temperature / 10.0,  # Convert 0-10 scale to 0-1
            max_tokens=agent_record.max_tokens,
            model=agent_record.model
        )
    )

    # Start the session first before dialing
    session_started = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                # Enable Krisp background voice and noise removal
                noise_cancellation=noise_cancellation.BVCTelephony(),
            ),
        )
    )

    # Create SIP participant to start dialing
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=sip_outbound_trunk_id,
                sip_call_to=phone_number,
                participant_identity=phone_number,
                # Function blocks until user answers the call, or if the call fails
                wait_until_answered=True,
            )
        )

        # Wait for the agent session start and participant join
        await session_started
        participant = await ctx.wait_for_participant(identity=phone_number)
        logger.info(f"Participant joined: {participant.identity}")

        agent.set_participant(participant)

        # Generate initial greeting
        await session.generate_reply(
            instructions="Greet the caller and offer your assistance."
        )

    except api.TwirpError as e:
        logger.error(
            f"Error creating SIP participant: {e.message}, "
            f"SIP status: {e.metadata.get('sip_status_code')} "
            f"{e.metadata.get('sip_status')}"
        )
        ctx.shutdown()
    except Exception as e:
        logger.error(f"Unexpected error in call worker: {e}")
        ctx.shutdown()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="voice-agent-worker",
        )
    ) 