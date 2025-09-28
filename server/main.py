from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import openai, silero
from agents.prompts import COOKING_ASSISTANT_PROMPT
from agents.tools import set_timer, send_recipe_name, save_recipe, set_ingredients, update_ingredients


load_dotenv()


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    agent = Agent(
        instructions=COOKING_ASSISTANT_PROMPT,
        tools=[set_timer, send_recipe_name, save_recipe, set_ingredients, update_ingredients],
    )
    session = AgentSession(
        vad=silero.VAD.load(),
        tts=openai.TTS(
            voice="fable",
            model="gpt-4o-mini-tts"
        ),
        stt=openai.STT(),
        llm=openai.LLM(
            model="gpt-4.1-nano"
        ),
    )

    await session.start(agent=agent, room=ctx.room)
    await session.generate_reply(
        instructions="greet the user and ask what they want to cook"
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
