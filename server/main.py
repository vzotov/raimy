import asyncio

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.plugins import openai, silero
from prompts import COOKING_ASSISTANT_PROMPT


load_dotenv()


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    agent = Agent(
        instructions=COOKING_ASSISTANT_PROMPT,
        tools=[
            llm.FunctionTool(
                name="set_timer",
                description="Set a timer for the user",
                parameters={
                    "type": "object",
                    "properties": {
                        "duration": {
                            "type": "number",
                            "description": "The number of seconds for the timer.",
                        },
                        "label": {
                            "type": "string",
                            "description": "A short label describing what the timer is for.",
                        },
                    },
                    "required": ["duration", "label"],
                },
            ),
            llm.FunctionTool(
                name="send_recipe_name",
                description="Send the selected recipe name to the client",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the selected recipe.",
                        },
                    },
                    "required": ["name"],
                },
            ),
            llm.FunctionTool(
                name="save_recipe",
                description="Save the completed recipe session",
                parameters={
                    "type": "object",
                    "properties": {
                        "recipe": {
                            "type": "object",
                            "description": "The recipe data to save.",
                        },
                    },
                    "required": ["recipe"],
                },
            ),
        ],
    )
    session = AgentSession(
        vad=silero.VAD.load(),
        tts=openai.TTS(
            voice="fable",
        ),
        stt=openai.STT(),
        llm=openai.LLM(),
    )

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(
        instructions="greet the user and ask what they want to cook"
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
