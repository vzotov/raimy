"""
Integration tests for meal planner session API routes
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from uuid import uuid4

from app.main import app
from app.routes.meal_planner_sessions import get_current_user_with_storage


# Mock authentication for tests
async def mock_get_current_user():
    """Mock authenticated user"""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/pic.jpg"
    }


@pytest.mark.integration
@pytest.mark.asyncio
class TestMealPlannerSessionRoutes:
    """Test meal planner session API endpoints"""

    async def test_create_session(self):
        """Test POST /api/meal-planner-sessions"""
        session_id = str(uuid4())
        mock_session = {
            "id": session_id,
            "user_id": "test@example.com",
            "session_name": "Untitled Session",
            "room_name": f"meal-planner-{session_id}",
            "messages": [],
            "created_at": "2024-01-01T00:00:00"
        }

        # Override dependency
        app.dependency_overrides[get_current_user_with_storage] = mock_get_current_user

        with patch("app.routes.meal_planner_sessions.database_service.create_meal_planner_session",
                   new=AsyncMock(return_value=mock_session)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/meal-planner-sessions")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Session created successfully"
            assert data["session"]["id"] == session_id
            assert data["session"]["session_name"] == "Untitled Session"

        # Clear overrides
        app.dependency_overrides.clear()

    async def test_list_sessions(self):
        """Test GET /api/meal-planner-sessions"""
        session_id_1 = str(uuid4())
        session_id_2 = str(uuid4())
        mock_sessions = [
            {
                "id": session_id_1,
                "user_id": "test@example.com",
                "session_name": "Thai Curry",
                "room_name": f"meal-planner-{session_id_1}",
                "created_at": "2024-01-02T00:00:00"
            },
            {
                "id": session_id_2,
                "user_id": "test@example.com",
                "session_name": "Pasta Night",
                "room_name": f"meal-planner-{session_id_2}",
                "created_at": "2024-01-01T00:00:00"
            }
        ]

        app.dependency_overrides[get_current_user_with_storage] = mock_get_current_user

        with patch("app.routes.meal_planner_sessions.database_service.get_user_meal_planner_sessions",
                   new=AsyncMock(return_value=mock_sessions)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/meal-planner-sessions")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
            assert len(data["sessions"]) == 2
            assert data["sessions"][0]["session_name"] == "Thai Curry"

        app.dependency_overrides.clear()

    async def test_get_session(self):
        """Test GET /api/meal-planner-sessions/{session_id}"""
        session_id = str(uuid4())
        mock_session = {
            "id": session_id,
            "user_id": "test@example.com",
            "session_name": "Thai Curry",
            "room_name": f"meal-planner-{session_id}",
            "messages": [
                {"role": "user", "content": "I want Thai curry", "timestamp": "2024-01-01T00:00:00"},
                {"role": "assistant", "content": "Great choice!", "timestamp": "2024-01-01T00:00:01"}
            ],
            "created_at": "2024-01-01T00:00:00"
        }

        app.dependency_overrides[get_current_user_with_storage] = mock_get_current_user

        with patch("app.routes.meal_planner_sessions.database_service.get_meal_planner_session",
                   new=AsyncMock(return_value=mock_session)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/meal-planner-sessions/{session_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["session"]["id"] == session_id
            assert len(data["session"]["messages"]) == 2

        app.dependency_overrides.clear()

    async def test_get_nonexistent_session(self):
        """Test GET /api/meal-planner-sessions/{session_id} with invalid ID"""
        session_id = str(uuid4())

        app.dependency_overrides[get_current_user_with_storage] = mock_get_current_user

        with patch("app.routes.meal_planner_sessions.database_service.get_meal_planner_session",
                   new=AsyncMock(return_value=None)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/meal-planner-sessions/{session_id}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

        app.dependency_overrides.clear()

    async def test_get_session_wrong_owner(self):
        """Test GET /api/meal-planner-sessions/{session_id} with wrong owner"""
        session_id = str(uuid4())
        mock_session = {
            "id": session_id,
            "user_id": "other@example.com",  # Different owner
            "session_name": "Thai Curry",
            "room_name": f"meal-planner-{session_id}",
            "messages": [],
            "created_at": "2024-01-01T00:00:00"
        }

        app.dependency_overrides[get_current_user_with_storage] = mock_get_current_user

        with patch("app.routes.meal_planner_sessions.database_service.get_meal_planner_session",
                   new=AsyncMock(return_value=mock_session)):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(f"/api/meal-planner-sessions/{session_id}")

            assert response.status_code == 403
            assert "denied" in response.json()["detail"].lower()

        app.dependency_overrides.clear()

    async def test_update_session_name(self):
        """Test PUT /api/meal-planner-sessions/{session_id}/name"""
        session_id = str(uuid4())
        mock_session = {
            "id": session_id,
            "user_id": "test@example.com",
            "session_name": "Untitled Session",
            "room_name": f"meal-planner-{session_id}",
            "messages": [],
            "created_at": "2024-01-01T00:00:00"
        }

        app.dependency_overrides[get_current_user_with_storage] = mock_get_current_user

        with patch("app.routes.meal_planner_sessions.database_service.get_meal_planner_session",
                   new=AsyncMock(return_value=mock_session)):
            with patch("app.routes.meal_planner_sessions.database_service.update_session_name",
                      new=AsyncMock(return_value=True)):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.put(
                        f"/api/meal-planner-sessions/{session_id}/name",
                        json={"session_name": "Thai Curry Recipe"}
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["session_name"] == "Thai Curry Recipe"
                assert "updated successfully" in data["message"]

        app.dependency_overrides.clear()

    async def test_delete_session(self):
        """Test DELETE /api/meal-planner-sessions/{session_id}"""
        session_id = str(uuid4())
        mock_session = {
            "id": session_id,
            "user_id": "test@example.com",
            "session_name": "Thai Curry",
            "room_name": f"meal-planner-{session_id}",
            "messages": [],
            "created_at": "2024-01-01T00:00:00"
        }

        app.dependency_overrides[get_current_user_with_storage] = mock_get_current_user

        with patch("app.routes.meal_planner_sessions.database_service.get_meal_planner_session",
                   new=AsyncMock(return_value=mock_session)):
            with patch("app.routes.meal_planner_sessions.database_service.delete_meal_planner_session",
                      new=AsyncMock(return_value=True)):
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.delete(f"/api/meal-planner-sessions/{session_id}")

                assert response.status_code == 200
                data = response.json()
                assert "deleted successfully" in data["message"]
                assert data["session_id"] == session_id

        app.dependency_overrides.clear()
