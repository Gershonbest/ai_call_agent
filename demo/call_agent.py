from __future__ import annotations

import asyncio
import logging
from dotenv import load_dotenv
import json
import os
from typing import Any


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
    google,
    deepgram,
    openai,
    cartesia,
    silero,
    noise_cancellation,  # noqa: F401
)
from livekit.plugins.turn_detector.english import EnglishModel
from prompt import set_instruction


# load environment variables, this is optional, only used for local development
load_dotenv(dotenv_path=".env")
logger = logging.getLogger("outbound-caller")
logger.setLevel(logging.INFO)
# os.environ.get("OPENAI_API_KEY")
openai_api_key=os.getenv('OPENAI_API_KEY')
outbound_trunk_id = os.environ.get("SIP_OUTBOUND_TRUNK_ID")
print(f"SIP TRUNK ID :  ::: ::: {outbound_trunk_id}")


class OutboundCaller(Agent):
    def __init__(
        self,
        *,
        agent_name: str,
        name: str,
        email: str,
        registeredon: str,
        interest: str,
        brand: str,
        dial_info: dict[str, Any],
    ):
        super().__init__(

            instructions=set_instruction(
                agent_name=agent_name, 
                brand=brand,
                name=name,
                email=email,
                registeredon=registeredon,
                interest=interest
            )
        )
        # keep reference to the participant for transfers
        self.participant: rtc.RemoteParticipant | None = None

        self.dial_info = dial_info

    def set_participant(self, participant: rtc.RemoteParticipant):
        self.participant = participant

    async def hangup(self):
        """Helper function to hang up the call by deleting the room"""

        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(
            api.DeleteRoomRequest(
                room=job_ctx.room.name,
            )
        )

    @function_tool()
    async def transfer_call(self, ctx: RunContext):
        """Transfer the call to a human agent, called after confirming with the user"""

        transfer_to = self.dial_info["transfer_to"]
        if not transfer_to:
            return "cannot transfer call"

        logger.info(f"transferring call to {transfer_to}")

        # let the message play fully before transferring
        await ctx.session.generate_reply(
            instructions="let the user know you'll be transferring them"
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

            logger.info(f"transferred call to {transfer_to}")
        except Exception as e:
            logger.error(f"error transferring call: {e}")
            await ctx.session.generate_reply(
                instructions="there was an error transferring the call."
            )
            await self.hangup()

    @function_tool()
    async def end_call(self, ctx: RunContext):
        """Called when the user wants to end the call"""
        logger.info(f"ending the call for {self.participant.identity}")

        # let the agent finish speaking
        current_speech = ctx.session.current_speech
        if current_speech:
            await current_speech.wait_for_playout()

        await self.hangup()

    @function_tool()
    async def look_up_availability(
        self,
        ctx: RunContext,
        date: str,
    ):
        """Called when the user asks about alternative appointment availability

        Args:
            date: The date of the appointment to check availability for
        """
        logger.info(
            f"looking up availability for {self.participant.identity} on {date}"
        )
        await asyncio.sleep(1)
        return {
            "available_times": ["1pm", "2pm", "3pm"],
        }

    @function_tool()
    async def book_appointment(
        ctx: RunContext,
        date: str,
        time: str,
        name: str,
        summary: str = "Appointment",
        description: str = "",
    ):
        """
        Simulates booking an appointment in Google Calendar.
        Use this only for testing or as a placeholder.

        Args:
            date: The date of the appointment (YYYY-MM-DD)
            time: The time of the appointment (HH:MM)
            name: The name of the client 
            summary: The title of the event
            description: Additional details for the event
        """
        logger.info(
            f"Booking Google Calendar event for {name} "
            f"on {date} at {time} with summary '{summary}'"
        )

        
        mock_event_url = f"https://calendar.google.com/event?mock=true&date={date}&time={time.replace(':', '')}"

        return f"appointment booked successfully: {mock_event_url}"

    @function_tool()
    async def detected_answering_machine(self, ctx: RunContext):
        """Called when the call reaches voicemail. Use this tool AFTER you hear the voicemail greeting"""
        logger.info(f"detected answering machine for {self.participant.identity}")
        await self.hangup()


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect()
    # This block attempts to start a recording (egress) of the room's audio.
    # The recording is saved to an S3 bucket.
    try:
        lkapi = api.LiveKitAPI()

        req = api.RoomCompositeEgressRequest(
            room_name=ctx.room.name,
            audio_only=True,
            file_outputs=[
                api.EncodedFileOutput(
                file_type=api.EncodedFileType.OGG,
                filepath=f"/tmp/{ctx.room.name}.ogg"
            )],
        )

        print("Starting room egress...")
        print("REQ:", req)

        egress_info = await lkapi.egress.start_room_composite_egress(req)
        await lkapi.aclose()

        egress_id = getattr(egress_info, "egress_id", None) or getattr(egress_info, "egressId", None)
        print(f"Egress started successfully. Egress ID: {egress_id}")

    except Exception as e:
        print(f"Error starting egress: {e}")
  
    dial_info = json.loads(ctx.job.metadata)
    participant_identity = phone_number = dial_info["phone_number"]
    lead_name = dial_info["lead_info"]["name"]
    agent_name = dial_info["agent_info"]["name"]
    email = dial_info["lead_info"]["email"]
    registeredon = dial_info["lead_info"]["registeredon"]
    interest = dial_info["lead_info"]["interest"]
    brand = dial_info["agent_info"]["brand"]
    

    agent = OutboundCaller(
        name=lead_name,
        email=email,
        agent_name=agent_name,
        registeredon=registeredon,
        interest=interest,
        brand=brand,
        dial_info=dial_info,
    )

    session = AgentSession(
        # turn_detection=EnglishModel(),
        # vad=silero.VAD.load(),
        # stt=deepgram.STT(),
        # you can also use OpenAI's TTS with openai.TTS()
        # tts=cartesia.TTS(),
        # llm=openai.LLM(model="gpt-4o"),
        # you can also use a speech-to-speech model like OpenAI's Realtime API
        # llm=openai.realtime.RealtimeModel(api_key=openai_api_key)
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Puck",
            temperature=0.8,
            instructions="You are a helpful assistant",
        ),
    )

    # start the session first before dialing, to ensure that when the user picks up
    # the agent does not miss anything the user says
    session_started = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                # enable Krisp background voice and noise removal
                noise_cancellation=noise_cancellation.BVCTelephony(),
            ),
        )
    )

    # `create_sip_participant` starts dialing the user
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=outbound_trunk_id,
                sip_call_to=phone_number,
                participant_identity=participant_identity,
                # function blocks until user answers the call, or if the call fails
                wait_until_answered=True,
            )
        )

        # wait for the agent session start and participant join
        await session_started
        participant = await ctx.wait_for_participant(identity=participant_identity)
        logger.info(f"participant joined: {participant.identity}")

        agent.set_participant(participant)

    except api.TwirpError as e:
        logger.error(
            f"error creating SIP participant: {e.message}, "
            f"SIP status: {e.metadata.get('sip_status_code')} "
            f"{e.metadata.get('sip_status')}"
        )
        ctx.shutdown()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="outbound-caller",
        )
    )