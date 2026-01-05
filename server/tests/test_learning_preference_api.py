"""
API tests for Learning Preference endpoints.
Tests all CRUD operations using httpx AsyncClient.
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app


# Test data fixtures
@pytest.fixture
def sample_preference_data():
    """Sample learning preference data in camelCase (as frontend sends)."""
    return {
        "webSearch": True,
        "youtubeSearch": False,
        "diagramsAndFlowcharts": True,
        "imagesAndIllustrations": True,
        "chartsAndGraphs": False,
        "mindMaps": True,
        "stepByStepExplanation": True,
        "workedExamples": False,
        "practiceProblems": True,
        "learnThroughStories": False,
        "explainWithRealWorldExamples": True,
        "analogiesAndComparisons": False,
        "funAndCuriousFacts": True,
        "handlingDifficulty": "break_down"
    }


@pytest.fixture
def sample_preference_data_snake_case():
    """Sample learning preference data in snake_case."""
    return {
        "web_search": True,
        "youtube_search": False,
        "diagrams_and_flowcharts": True,
        "images_and_illustrations": True,
        "charts_and_graphs": False,
        "mind_maps": True,
        "step_by_step_explanation": True,
        "worked_examples": False,
        "practice_problems": True,
        "learn_through_stories": False,
        "explain_with_real_world_examples": True,
        "analogies_and_comparisons": False,
        "fun_and_curious_facts": True,
        "handling_difficulty": "break_down"
    }


@pytest.fixture
def updated_preference_data():
    """Updated learning preference data."""
    return {
        "webSearch": False,
        "youtubeSearch": True,
        "diagramsAndFlowcharts": False,
        "imagesAndIllustrations": False,
        "chartsAndGraphs": True,
        "mindMaps": False,
        "stepByStepExplanation": False,
        "workedExamples": True,
        "practiceProblems": False,
        "learnThroughStories": True,
        "explainWithRealWorldExamples": False,
        "analogiesAndComparisons": True,
        "funAndCuriousFacts": False,
        "handlingDifficulty": "simplify"
    }


@pytest.fixture
def test_user_id():
    """Test user ID for authentication."""
    return "test_user_123"


@pytest.fixture
def auth_headers(test_user_id):
    """Authentication headers with X-User-ID."""
    return {"X-User-ID": test_user_id}


class TestCreateLearningConfig:
    """Test cases for POST /api/v1/learnconfig/create endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_learning_config_success(
        self, 
        sample_preference_data, 
        auth_headers
    ):
        """Test successful creation of learning preferences."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            
            # Verify response structure
            assert "id" in data
            assert "userId" in data
            assert data["userId"] == auth_headers["X-User-ID"]
            assert "createdAt" in data
            assert "updatedAt" in data
            
            # Verify all preference fields are returned
            assert data["webSearch"] == sample_preference_data["webSearch"]
            assert data["youtubeSearch"] == sample_preference_data["youtubeSearch"]
            assert data["diagramsAndFlowcharts"] == sample_preference_data["diagramsAndFlowcharts"]
            assert data["imagesAndIllustrations"] == sample_preference_data["imagesAndIllustrations"]
            assert data["chartsAndGraphs"] == sample_preference_data["chartsAndGraphs"]
            assert data["mindMaps"] == sample_preference_data["mindMaps"]
            assert data["stepByStepExplanation"] == sample_preference_data["stepByStepExplanation"]
            assert data["workedExamples"] == sample_preference_data["workedExamples"]
            assert data["practiceProblems"] == sample_preference_data["practiceProblems"]
            assert data["learnThroughStories"] == sample_preference_data["learnThroughStories"]
            assert data["explainWithRealWorldExamples"] == sample_preference_data["explainWithRealWorldExamples"]
            assert data["analogiesAndComparisons"] == sample_preference_data["analogiesAndComparisons"]
            assert data["funAndCuriousFacts"] == sample_preference_data["funAndCuriousFacts"]
            assert data["handlingDifficulty"] == sample_preference_data["handlingDifficulty"]
    
    @pytest.mark.asyncio
    async def test_create_learning_config_with_snake_case(
        self, 
        sample_preference_data_snake_case, 
        auth_headers
    ):
        """Test creation with snake_case field names."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data_snake_case,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["userId"] == auth_headers["X-User-ID"]
            assert isinstance(data["id"], int)
    
    @pytest.mark.asyncio
    async def test_create_learning_config_without_auth(self, sample_preference_data):
        """Test creation fails without authentication header."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data
            )
            
            assert response.status_code == 422  # FastAPI validation error for missing header
    
    @pytest.mark.asyncio
    async def test_create_learning_config_with_empty_auth(self, sample_preference_data):
        """Test creation fails with empty authentication header."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data,
                headers={"X-User-ID": ""}
            )
            
            assert response.status_code == 401
            assert "User ID is required" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_learning_config_minimal_data(self, auth_headers):
        """Test creation with minimal/default data."""
        minimal_data = {
            "webSearch": False,
            "youtubeSearch": False
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/create",
                json=minimal_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["webSearch"] is False
            assert data["youtubeSearch"] is False


class TestGetLearningConfig:
    """Test cases for GET /api/v1/learnconfig endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_learning_config_success(
        self, 
        sample_preference_data, 
        auth_headers,
        test_user_id
    ):
        """Test successful retrieval of learning preferences."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First create a preference
            create_response = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            created_data = create_response.json()
            
            # Then retrieve it
            get_response = await client.get(
                "/api/v1/learnconfig",
                headers=auth_headers
            )
            
            assert get_response.status_code == 200
            data = get_response.json()
            
            # Verify retrieved data matches created data
            assert data["id"] == created_data["id"]
            assert data["userId"] == test_user_id
            assert data["webSearch"] == sample_preference_data["webSearch"]
            assert data["youtubeSearch"] == sample_preference_data["youtubeSearch"]
    
    @pytest.mark.asyncio
    async def test_get_learning_config_not_found(self, auth_headers):
        """Test retrieval when preferences don't exist."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/learnconfig",
                headers={"X-User-ID": "non_existent_user"}
            )
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_learning_config_without_auth(self):
        """Test retrieval fails without authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/learnconfig")
            
            assert response.status_code == 422


class TestUpdateLearningConfig:
    """Test cases for PUT /api/v1/learnconfig/update/ endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_learning_config_success(
        self, 
        sample_preference_data, 
        updated_preference_data,
        auth_headers,
        test_user_id
    ):
        """Test successful update of learning preferences."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First create a preference
            create_response = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            created_id = create_response.json()["id"]
            
            # Then update it
            update_response = await client.put(
                "/api/v1/learnconfig/update/",
                json=updated_preference_data,
                headers=auth_headers
            )
            
            assert update_response.status_code == 200
            data = update_response.json()
            
            # Verify updated data
            assert data["id"] == created_id
            assert data["userId"] == test_user_id
            assert data["webSearch"] == updated_preference_data["webSearch"]
            assert data["youtubeSearch"] == updated_preference_data["youtubeSearch"]
            assert data["handlingDifficulty"] == updated_preference_data["handlingDifficulty"]
    
    @pytest.mark.asyncio
    async def test_update_learning_config_creates_if_not_exists(
        self, 
        sample_preference_data,
        auth_headers,
        test_user_id
    ):
        """Test update creates preference if it doesn't exist (upsert behavior)."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Update without creating first
            update_response = await client.put(
                "/api/v1/learnconfig/update/",
                json=sample_preference_data,
                headers=auth_headers
            )
            
            assert update_response.status_code == 200
            data = update_response.json()
            assert data["userId"] == test_user_id
            assert isinstance(data["id"], int)
    
    @pytest.mark.asyncio
    async def test_update_learning_config_without_auth(self, updated_preference_data):
        """Test update fails without authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/learnconfig/update/",
                json=updated_preference_data
            )
            
            assert response.status_code == 422


class TestUpsertLearningConfig:
    """Test cases for POST /api/v1/learnconfig/upsert endpoint."""
    
    @pytest.mark.asyncio
    async def test_upsert_learning_config_create(
        self, 
        sample_preference_data,
        auth_headers,
        test_user_id
    ):
        """Test upsert creates new preference when it doesn't exist."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/upsert",
                json=sample_preference_data,
                headers={"X-User-ID": "new_user_456"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["userId"] == "new_user_456"
            assert isinstance(data["id"], int)
    
    @pytest.mark.asyncio
    async def test_upsert_learning_config_update(
        self, 
        sample_preference_data,
        updated_preference_data,
        auth_headers,
        test_user_id
    ):
        """Test upsert updates existing preference."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First create
            create_response = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data,
                headers=auth_headers
            )
            created_id = create_response.json()["id"]
            
            # Then upsert with updated data
            upsert_response = await client.post(
                "/api/v1/learnconfig/upsert",
                json=updated_preference_data,
                headers=auth_headers
            )
            
            assert upsert_response.status_code == 200
            data = upsert_response.json()
            assert data["id"] == created_id
            assert data["webSearch"] == updated_preference_data["webSearch"]
    
    @pytest.mark.asyncio
    async def test_upsert_learning_config_without_auth(self, sample_preference_data):
        """Test upsert fails without authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/upsert",
                json=sample_preference_data
            )
            
            assert response.status_code == 422


class TestLearningConfigWorkflow:
    """Integration tests for complete workflow."""
    
    @pytest.mark.asyncio
    async def test_full_crud_workflow(
        self, 
        sample_preference_data, 
        updated_preference_data,
        auth_headers,
        test_user_id
    ):
        """Test complete CRUD workflow: Create -> Read -> Update -> Read."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 1. Create
            create_response = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data,
                headers=auth_headers
            )
            assert create_response.status_code == 201
            created_data = create_response.json()
            created_id = created_data["id"]
            
            # 2. Read
            get_response = await client.get(
                "/api/v1/learnconfig",
                headers=auth_headers
            )
            assert get_response.status_code == 200
            assert get_response.json()["id"] == created_id
            
            # 3. Update
            update_response = await client.put(
                "/api/v1/learnconfig/update/",
                json=updated_preference_data,
                headers=auth_headers
            )
            assert update_response.status_code == 200
            updated_data = update_response.json()
            assert updated_data["id"] == created_id
            assert updated_data["webSearch"] == updated_preference_data["webSearch"]
            
            # 4. Read again to verify update
            get_response2 = await client.get(
                "/api/v1/learnconfig",
                headers=auth_headers
            )
            assert get_response2.status_code == 200
            assert get_response2.json()["webSearch"] == updated_preference_data["webSearch"]
    
    @pytest.mark.asyncio
    async def test_user_isolation(
        self, 
        sample_preference_data,
        auth_headers
    ):
        """Test that users can only access their own preferences."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create preference for user 1
            user1_headers = {"X-User-ID": "user1"}
            create_response1 = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data,
                headers=user1_headers
            )
            assert create_response1.status_code == 201
            user1_id = create_response1.json()["id"]
            
            # Create preference for user 2
            user2_headers = {"X-User-ID": "user2"}
            create_response2 = await client.post(
                "/api/v1/learnconfig/create",
                json=sample_preference_data,
                headers=user2_headers
            )
            assert create_response2.status_code == 201
            user2_id = create_response2.json()["id"]
            
            # Verify users get their own preferences
            get_response1 = await client.get(
                "/api/v1/learnconfig",
                headers=user1_headers
            )
            assert get_response1.status_code == 200
            assert get_response1.json()["id"] == user1_id
            assert get_response1.json()["userId"] == "user1"
            
            get_response2 = await client.get(
                "/api/v1/learnconfig",
                headers=user2_headers
            )
            assert get_response2.status_code == 200
            assert get_response2.json()["id"] == user2_id
            assert get_response2.json()["userId"] == "user2"
            
            # Verify IDs are different
            assert user1_id != user2_id


class TestLearningConfigEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_create_with_all_false(self, auth_headers):
        """Test creating preferences with all boolean fields set to False."""
        all_false_data = {
            "webSearch": False,
            "youtubeSearch": False,
            "diagramsAndFlowcharts": False,
            "imagesAndIllustrations": False,
            "chartsAndGraphs": False,
            "mindMaps": False,
            "stepByStepExplanation": False,
            "workedExamples": False,
            "practiceProblems": False,
            "learnThroughStories": False,
            "explainWithRealWorldExamples": False,
            "analogiesAndComparisons": False,
            "funAndCuriousFacts": False
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/create",
                json=all_false_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["webSearch"] is False
            assert data["youtubeSearch"] is False
    
    @pytest.mark.asyncio
    async def test_create_with_all_true(self, auth_headers):
        """Test creating preferences with all boolean fields set to True."""
        all_true_data = {
            "webSearch": True,
            "youtubeSearch": True,
            "diagramsAndFlowcharts": True,
            "imagesAndIllustrations": True,
            "chartsAndGraphs": True,
            "mindMaps": True,
            "stepByStepExplanation": True,
            "workedExamples": True,
            "practiceProblems": True,
            "learnThroughStories": True,
            "explainWithRealWorldExamples": True,
            "analogiesAndComparisons": True,
            "funAndCuriousFacts": True,
            "handlingDifficulty": "break_down"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/create",
                json=all_true_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["webSearch"] is True
            assert data["youtubeSearch"] is True
    
    @pytest.mark.asyncio
    async def test_create_with_null_handling_difficulty(self, auth_headers):
        """Test creating preferences with null handlingDifficulty."""
        data_with_null = {
            "webSearch": True,
            "youtubeSearch": False,
            "handlingDifficulty": None
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/learnconfig/create",
                json=data_with_null,
                headers=auth_headers
            )
            
            # Should succeed with None handlingDifficulty
            assert response.status_code == 201
            data = response.json()
            assert data["handlingDifficulty"] is None or data.get("handlingDifficulty") is None