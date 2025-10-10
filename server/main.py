import os
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    RoomInputOptions,
    RoomOutputOptions,
)
from livekit.agents.llm.mcp import MCPServerHTTP
from livekit.plugins import openai, silero
from agents.prompts import (
    COOKING_ASSISTANT_PROMPT,
    MEAL_PLANNER_PROMPT,
    COOKING_GREETING,
    MEAL_PLANNER_GREETING,
)


load_dotenv()


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Initialize MCP server connection
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp-service:8002/mcp")
    mcp_server = MCPServerHTTP(url=mcp_server_url)
    await mcp_server.initialize()

    # Get tools from MCP server
    mcp_tools = await mcp_server.list_tools()

    # Determine which prompt to use based on room name
    is_meal_planner = ctx.room.name.startswith("meal-planner")
    prompt = MEAL_PLANNER_PROMPT if is_meal_planner else COOKING_ASSISTANT_PROMPT
    greeting_instructions = MEAL_PLANNER_GREETING if is_meal_planner else COOKING_GREETING

    agent = Agent(
        instructions=prompt,
        tools=mcp_tools,  # Use tools from MCP server
    )

    # Configure session based on room type
    if is_meal_planner:
        # Text-only session for meal planner
        session = AgentSession(
            llm=openai.LLM(
                model="gpt-5-mini"
            ),
        )

        await session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(audio_enabled=False),
            room_output_options=RoomOutputOptions(audio_enabled=False, transcription_enabled=True),
        )

        print(f"[DEBUG] Text-only session started for meal planner")
        print(f"[DEBUG] Generating greeting with instructions: {greeting_instructions}")
    else:
        # Voice session for cooking assistant
        session = AgentSession(
            vad=silero.VAD.load(),
            tts=openai.TTS(
                voice="fable",
                model="gpt-4o-mini-tts"
            ),
            stt=openai.STT(),
            llm=openai.LLM(
                model="gpt-5-mini"
            ),
        )
        await session.start(agent=agent, room=ctx.room)

    await session.generate_reply(instructions=greeting_instructions)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
