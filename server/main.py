import os
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.agents.llm.mcp import MCPServerHTTP
from livekit.plugins import openai, silero
from agents.prompts import COOKING_ASSISTANT_PROMPT


load_dotenv()


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Initialize MCP server connection
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp-service:8002/mcp")
    mcp_server = MCPServerHTTP(url=mcp_server_url)
    await mcp_server.initialize()

    # Get tools from MCP server
    mcp_tools = await mcp_server.list_tools()

    agent = Agent(
        instructions=COOKING_ASSISTANT_PROMPT,
        tools=mcp_tools,  # Use tools from MCP server
    )
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
    await session.generate_reply(
        instructions="greet the user and ask what they want to cook"
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
