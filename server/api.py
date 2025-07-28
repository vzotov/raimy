import asyncio
import json
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import uvicorn

from firebase_service import firebase_service, Recipe, RecipeStep

# Data models
class TimerRequest(BaseModel):
    duration: int
    label: str


class RecipeNameRequest(BaseModel):
    recipe_name: str


class SaveRecipeRequest(BaseModel):
    name: str
    description: Optional[str] = None
    ingredients: List[str]
    steps: List[dict]  # Will be converted to RecipeStep objects
    total_time_minutes: Optional[int] = None
    difficulty: Optional[str] = None
    servings: Optional[int] = None
    tags: Optional[List[str]] = None
    user_id: Optional[str] = None


# Global state for SSE connections
sse_connections: List[asyncio.Queue] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting FastAPI server...")
    yield
    print("Shutting down FastAPI server...")


app = FastAPI(
    title="Raimy Cooking Assistant API",
    description="API for the Raimy cooking assistant with real-time SSE communication",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def broadcast_event(event_type: str, data: dict):
    """Broadcast event to all connected SSE clients"""
    event_data = {
        "type": event_type,
        "data": data
    }
    
    # Remove disconnected clients
    disconnected = []
    for i, queue in enumerate(sse_connections):
        try:
            await queue.put(json.dumps(event_data))
        except Exception:
            disconnected.append(i)
    
    # Remove disconnected clients
    for i in reversed(disconnected):
        sse_connections.pop(i)


@app.get("/")
async def root():
    return {"message": "Raimy Cooking Assistant API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "connections": len(sse_connections)}


@app.post("/api/timers/set")
async def set_timer(timer: TimerRequest):
    """Set a timer for the current cooking step"""
    timer_data = {
        "duration": timer.duration,
        "label": timer.label,
        "started_at": asyncio.get_event_loop().time()
    }
    
    # Broadcast timer set event
    await broadcast_event("timer_set", timer_data)
    
    return {"message": f"Timer set for {timer.duration} seconds: {timer.label}"}


@app.post("/api/recipes/name")
async def send_recipe_name(recipe: RecipeNameRequest):
    """Send recipe name to the client via SSE"""
    recipe_data = {
        "recipe_name": recipe.recipe_name,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # Broadcast recipe name event
    await broadcast_event("recipe_name", recipe_data)
    
    return {"message": f"Recipe name sent: {recipe.recipe_name}"}


# Recipe API endpoints
@app.get("/api/recipes")
async def get_recipes():
    """Get all recipes from the database"""
    try:
        recipes = await firebase_service.get_recipes()
        return {
            "recipes": recipes,
            "count": len(recipes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recipes: {str(e)}")


@app.post("/api/recipes")
async def save_recipe(recipe_request: SaveRecipeRequest):
    """Save a new recipe"""
    try:
        # Convert steps to RecipeStep objects
        steps = []
        for i, step_data in enumerate(recipe_request.steps):
            step = RecipeStep(
                step_number=i + 1,
                instruction=step_data.get("instruction", ""),
                duration_minutes=step_data.get("duration_minutes"),
                ingredients=step_data.get("ingredients")
            )
            steps.append(step)
        
        # Create Recipe object
        recipe = Recipe(
            name=recipe_request.name,
            description=recipe_request.description,
            ingredients=recipe_request.ingredients,
            steps=steps,
            total_time_minutes=recipe_request.total_time_minutes,
            difficulty=recipe_request.difficulty,
            servings=recipe_request.servings,
            tags=recipe_request.tags,
            user_id=recipe_request.user_id
        )
        
        # Save to Firebase
        recipe_id = await firebase_service.save_recipe(recipe)
        
        return {
            "message": "Recipe saved successfully",
            "recipe_id": recipe_id,
            "recipe": recipe.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save recipe: {str(e)}")


@app.get("/api/events")
async def events():
    """SSE endpoint for real-time events"""
    queue = asyncio.Queue()
    sse_connections.append(queue)
    
    async def event_generator():
        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": "message",
                        "data": data
                    }
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {
                        "event": "ping",
                        "data": "keepalive"
                    }
        except Exception as e:
            print(f"SSE connection error: {e}")
        finally:
            if queue in sse_connections:
                sse_connections.remove(queue)
    
    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 