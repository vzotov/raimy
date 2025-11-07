import os
import sys
import asyncio
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
    ChatContext,
)
from livekit.agents.llm.mcp import MCPServerHTTP
from livekit.plugins import openai, silero
from agents.prompts import (
    COOKING_ASSISTANT_PROMPT,
    MEAL_PLANNER_PROMPT,
    COOKING_GREETING,
    MEAL_PLANNER_GREETING,
)

# Import database service
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from app.services import database_service

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

    # For meal planner, restore chat context from database
    chat_ctx = None
    if is_meal_planner:
        # Extract session ID from room name (format: meal-planner-{uuid})
        session_id = ctx.room.name.replace("meal-planner-", "")

        try:
            # Load session from database
            session_data = await database_service.get_meal_planner_session(session_id)

            if session_data and session_data.get("messages"):
                # Restore ChatContext from saved messages
                chat_ctx = ChatContext.empty()
                for msg in session_data["messages"]:
                    chat_ctx.add_message(
                        role=msg["role"],
                        content=msg["content"]
                    )
        except Exception as e:
            print(f"Error loading meal planner session: {e}")
            # Continue with empty context if loading fails

    # Create agent with restored context (if any)
    agent = Agent(
        instructions=prompt,
        tools=mcp_tools,
        chat_ctx=chat_ctx,
    )

    # Configure session based on room type
    if is_meal_planner:
        # Text-only session for meal planner
        session = AgentSession(
            llm=openai.LLM(
                model="gpt-5-mini"
            ),
        )

        # Hook into conversation events to save messages to database
        @session.on("conversation_item_added")
        def on_message_added(event):
            async def save_message():
                try:
                    # Extract session ID from room name
                    msg_session_id = ctx.room.name.replace("meal-planner-", "")

                    # Skip if no text content
                    if not event.item.text_content:
                        return

                    # Save message to database
                    await database_service.add_message_to_session(
                        session_id=msg_session_id,
                        role=event.item.role,
                        content=event.item.text_content
                    )
                    print(f"[Meal Planner] Saved {event.item.role} message to session {msg_session_id}")
                except Exception as e:
                    print(f"[Meal Planner] Error saving message: {e}")
                    import traceback
                    traceback.print_exc()

            # Create task to run async function
            asyncio.create_task(save_message())

        await session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(audio_enabled=False),
            room_output_options=RoomOutputOptions(audio_enabled=False, transcription_enabled=True),
        )

        # If we restored messages and last message is from user, generate a reply
        if chat_ctx and len(chat_ctx.items) > 0:
            last_message = chat_ctx.items[-1]
            if last_message.role == "user":
                await session.generate_reply()
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

        # Send greeting for voice cooking assistant
        await session.generate_reply(instructions=greeting_instructions)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
