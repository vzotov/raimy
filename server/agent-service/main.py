"""
Raimy Agent Service

FastAPI service for chat agent orchestration with LangGraph.
"""
import logging
from typing import Optional, List, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app.services import database_service
from agents.registry import get_agent

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Raimy Agent Service",
    description="LangGraph-based agent service for chat and cooking assistance",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    structured_outputs: List[Dict] = []
    message_id: Optional[str] = None
    session_id: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agent", "version": "3.0.0"}


@app.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """
    Chat endpoint that processes messages using LangGraph agent.

    Steps:
    1. Load session context from database
    2. Get appropriate agent based on session type
    3. Run agent to generate response
    4. Save messages to database
    5. Return agent response
    """
    try:
        # Get session from database
        session_data = await database_service.get_chat_session(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Extract session info
        messages = session_data.get("messages", [])
        session_type = session_data.get("session_type", "recipe-creator")

        # Load recipe data if recipe_id is present (for kitchen sessions)
        recipe_id = session_data.get("recipe_id")
        if recipe_id:
            logger.info(f"🍳 Loading recipe {recipe_id} for kitchen session")
            recipe_data = await database_service.get_recipe_by_id(recipe_id)
            if recipe_data:
                session_data["recipe"] = recipe_data
                logger.info(f"✅ Loaded recipe: {recipe_data.get('name')}")
            else:
                logger.error(f"❌ Recipe {recipe_id} not found")

        # Save user message to database
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="user",
            content={"type": "text", "content": request.message},
        )

        # Get agent for this session type (cached)
        agent = await get_agent(session_type=session_type)

        # Run agent with streaming
        agent_result = await agent.run_streaming(
            message=request.message,
            message_history=messages,
            session_id=request.session_id,
            session_data=session_data,
        )

        # Save agent text response to database
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="assistant",
            content={"type": "text", "content": agent_result.text},
        )

        # Save structured recipe messages
        for recipe_data in agent_result.structured_outputs:
            recipe_message = {
                "type": "recipe",
                "recipe_id": recipe_data.get("recipe_id"),
                "name": recipe_data.get("name"),
                "description": recipe_data.get("description"),
                "ingredients": [
                    {"name": ing} for ing in recipe_data.get("ingredients", [])
                ],
                "steps": [
                    {
                        "step_number": i + 1,
                        "instruction": step.get("instruction", ""),
                        "duration_minutes": step.get("duration_minutes"),
                    }
                    for i, step in enumerate(recipe_data.get("steps", []))
                ],
                "total_time_minutes": recipe_data.get("total_time_minutes"),
                "difficulty": recipe_data.get("difficulty"),
                "servings": recipe_data.get("servings"),
                "tags": recipe_data.get("tags", []),
            }
            await database_service.add_message_to_session(
                session_id=request.session_id,
                role="assistant",
                content=recipe_message,
            )

        return ChatResponse(
            response=agent_result.text,
            structured_outputs=agent_result.structured_outputs,
            message_id=agent_result.message_id,
            session_id=request.session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent_chat: {e}", exc_info=True)

        # Publish error to Redis (import from shared server/core module)
        try:
            from core.redis_client import get_redis_client

            redis_client = get_redis_client()
            await redis_client.publish(
                f"session:{request.session_id}",
                {
                    "type": "system",
                    "content": {
                        "type": "error",
                        "message": "An error occurred processing your message",
                    },
                },
            )
        except Exception as redis_error:
            logger.error(f"Failed to publish error to Redis: {redis_error}")

        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True, log_level="info")
