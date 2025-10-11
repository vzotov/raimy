import os
from dotenv import load_dotenv
from datetime import datetime
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
    ChatMessage,
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
import sys
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

    # For meal planner, load session from database and restore context
    chat_ctx = None
    session_id = None
    session_data = None
    message_count = 0

    if is_meal_planner:
        # Extract session ID from room name (format: meal-planner-{uuid})
        session_id = ctx.room.name.replace("meal-planner-", "")
        print(f"[Meal Planner] Loading session: {session_id}")

        try:
            # Load session from database
            session_data = await database_service.get_meal_planner_session(session_id)

            if session_data and session_data.get("messages"):
                # Restore ChatContext from saved messages
                chat_ctx = ChatContext.empty()
                for msg in session_data["messages"]:
                    chat_ctx.messages.append(ChatMessage(
                        role=msg["role"],
                        content=msg["content"]
                    ))
                message_count = len(session_data["messages"])
                print(f"[Meal Planner] Restored {message_count} messages from session")
        except Exception as e:
            print(f"[Meal Planner] Error loading session: {e}")
            # Continue with empty context if loading fails

    # Create agent with restored context (if any)
    agent = Agent(
        instructions=prompt,
        tools=mcp_tools,
        chat_ctx=chat_ctx  # Will be None for cooking assistant or empty chat_ctx for new meal planner sessions
    )

    # Configure session based on room type
    if is_meal_planner:
        # Text-only session for meal planner
        session = AgentSession(
            llm=openai.LLM(
                model="gpt-5-mini"
            ),
        )

        # Hook into conversation_item_added for auto-save
        @session.on("conversation_item_added")
        async def on_message_added(event):
            try:
                message = {
                    "role": event.item.role,
                    "content": event.item.text_content,
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Save message to database
                success = await database_service.append_session_message(session_id, message)
                if success:
                    nonlocal message_count
                    message_count += 1
                    print(f"[Meal Planner] Saved message {message_count} to session {session_id}")

                    # After 3 messages, check if session needs naming (if still "Untitled Session")
                    if message_count == 3 and session_data and session_data.get("session_name") == "Untitled Session":
                        print(f"[Meal Planner] Session reached 3 messages - LLM should generate name")
                else:
                    print(f"[Meal Planner] Failed to save message to session")
            except Exception as e:
                print(f"[Meal Planner] Error in conversation_item_added hook: {e}")

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
