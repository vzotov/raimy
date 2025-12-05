import os
import sys
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services import database_service  # type: ignore
from agents.prompts import COOKING_ASSISTANT_PROMPT, MEAL_PLANNER_PROMPT  # type: ignore
from agents.langgraph_agent import LangGraphAgent  # type: ignore
from agents.mcp_tools import load_mcp_tools_for_langchain  # type: ignore

load_dotenv()

# Cache of agent instances by session type
agent_instances: Dict[str, LangGraphAgent] = {}


async def get_agent(session_type: str = "meal-planner") -> LangGraphAgent:
    """
    Get or create LangGraph agent instance for the specified session type

    Args:
        session_type: Session type ("kitchen" or "meal-planner")

    Returns:
        LangGraphAgent instance with session-type-specific tools
    """
    global agent_instances

    # Validate session_type and default to meal-planner if unknown
    if session_type not in {"kitchen", "meal-planner"}:
        print(f"⚠️  Unknown session_type '{session_type}', defaulting to 'meal-planner'")
        session_type = "meal-planner"

    # Return cached instance if exists
    if session_type in agent_instances:
        return agent_instances[session_type]

    # Create new agent instance with filtered tools
    print(f"🔄 Creating new agent instance for session_type='{session_type}'")
    mcp_tools = await load_mcp_tools_for_langchain(session_type=session_type)

    agent = LangGraphAgent(mcp_tools=mcp_tools)
    agent_instances[session_type] = agent

    print(f"✅ Initialized LangGraph agent for '{session_type}' with {len(mcp_tools)} tools")
    return agent


# FastAPI app
app = FastAPI(
    title="Raimy Agent Service",
    description="LangGraph-based agent service for chat and cooking assistance",
    version="2.0.0",
)

# Add CORS middleware
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
    structured_outputs: List[Dict] = []  # Recipe messages and other structured data
    message_id: Optional[str] = None
    session_id: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agent",
        "version": "2.0.0"
    }


@app.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """
    Chat endpoint that processes messages using LangGraph agent

    Steps:
    1. Load session context from database
    2. Add user message to context (if not empty session auto-greeting)
    3. Run LangGraph agent to generate response
    4. Save both user message and agent response to database
    5. Return agent response
    """
    try:
        # Get session from database
        session_data = await database_service.get_meal_planner_session(request.session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Extract message history
        messages = session_data.get("messages", [])

        # Read session type from database
        session_type = session_data.get("session_type", "meal-planner")

        # Extract ingredients if present
        ingredients = session_data.get("ingredients", [])

        # Select appropriate prompt based on session type
        if session_type == "kitchen":
            system_prompt = COOKING_ASSISTANT_PROMPT

            # If resuming session with ingredients, add context
            if ingredients:
                ingredient_context = "\n\n**CURRENT SESSION STATE:**\n"
                ingredient_context += f"Ingredients for this recipe ({len(ingredients)} total):\n"
                for ing in ingredients:
                    status = ""
                    if ing.get("used"):
                        status = " [USED]"
                    elif ing.get("highlighted"):
                        status = " [CURRENTLY USING]"
                    ingredient_context += f"- {ing['name']}: {ing.get('amount', '')} {ing.get('unit', '')}{status}\n"
                ingredient_context += "\nContinue guiding from where the session left off.\n"
                system_prompt = system_prompt + ingredient_context

        elif session_type == "meal-planner":
            system_prompt = MEAL_PLANNER_PROMPT
        else:
            # Default to meal-planner for unknown types
            system_prompt = MEAL_PLANNER_PROMPT

        # Save user message to database first
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="user",
            content=request.message
        )

        # Get LangGraph agent instance with session-type-specific tools
        agent = await get_agent(session_type=session_type)

        # Run agent with streaming to generate response
        agent_result = await agent.run_streaming(
            message=request.message,
            message_history=messages,
            system_prompt=system_prompt,
            session_id=request.session_id
        )

        # Extract response and structured outputs
        agent_response = agent_result["response"]
        structured_outputs = agent_result.get("structured_outputs", [])

        # Save agent text response to database
        await database_service.add_message_to_session(
            session_id=request.session_id,
            role="assistant",
            content=agent_response
        )

        # If there are saved recipes, create structured messages for each
        for recipe_data in structured_outputs:
            # Transform recipe data into frontend-compatible format
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
                        "duration_minutes": step.get("duration_minutes")
                    }
                    for i, step in enumerate(recipe_data.get("steps", []))
                ],
                "total_time_minutes": recipe_data.get("total_time_minutes"),
                "difficulty": recipe_data.get("difficulty"),
                "servings": recipe_data.get("servings"),
                "tags": recipe_data.get("tags", [])
            }

            # Save structured recipe message to database
            await database_service.add_message_to_session(
                session_id=request.session_id,
                role="assistant",
                content=recipe_message
            )

        return ChatResponse(
            response=agent_response,
            structured_outputs=structured_outputs,
            session_id=request.session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in agent_chat: {e}")
        import traceback
        traceback.print_exc()

        # Publish error to Redis so UI knows
        try:
            from core.redis_client import get_redis_client
            redis = get_redis_client()
            await redis.publish(
                f"session:{request.session_id}",
                {
                    "type": "system",
                    "content": {
                        "type": "error",
                        "message": "An error occurred processing your message"
                    }
                }
            )
        except Exception as redis_error:
            print(f"Failed to publish error to Redis: {redis_error}")

        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )