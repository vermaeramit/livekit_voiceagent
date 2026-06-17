import logging

from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import sarvam

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)


class VoiceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful voice assistant.
                Speak naturally as if you're having a real conversation.
                Keep replies SHORT — usually 1-2 sentences. Only give a longer
                answer when the user explicitly asks for detail. Get to the point
                quickly; this is a live voice call, so brevity matters for latency.
            """,
            # Saaras v3 STT — speech to text (language="unknown" auto-detects)
            stt=sarvam.STT(
                language="unknown",
                model="saaras:v3",
                mode="transcribe",
                flush_signal=True,
            ),
            # Sarvam LLM — generates responses
            llm=sarvam.LLM(model="sarvam-30b"),
            # Bulbul v3 TTS — text to speech
            # Female: priya, simran, ishita, kavya | Male: aditya, anand, rohan, shubh
            tts=sarvam.TTS(
                target_language_code="en-IN",
                model="bulbul:v3",
                speaker="shubh",
            ),
        )

    async def on_enter(self):
        """Called when the user joins — the agent opens the conversation."""
        self.session.generate_reply()


async def entrypoint(ctx: JobContext):
    """LiveKit calls this when a user connects to a room."""
    logger.info(f"User connected to room: {ctx.room.name}")

    session = AgentSession(
        turn_detection="stt",
        min_endpointing_delay=0.07,
        # Start generating the reply on the interim transcript, before the user
        # fully finishes — hides most of the LLM "thinking" latency.
        preemptive_generation=True,
    )
    await session.start(
        agent=VoiceAgent(),
        room=ctx.room,
    )


if __name__ == "__main__":
    # agent_name enables EXPLICIT dispatch: the agent joins only when a client
    # requests it by name (via RoomConfiguration in the token — see token_server.py).
    # This is reliable regardless of room-creation timing, unlike automatic dispatch.
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="voice-agent"))
