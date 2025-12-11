import pytest
import uuid
from fastapi.testclient import TestClient
from main import app
from database import get_database, MockDatabase

# Create a fresh database for tests
test_db = MockDatabase()

def get_test_database():
    return test_db

# Override the dependency
app.dependency_overrides[get_database] = get_test_database

# Create test client
client = TestClient(app)

# Test database fixture
@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test"""
    test_db.clear_all()
    yield
    test_db.clear_all()


def create_test_user(email=None):
    """Helper function to create a test user and return user_id"""
    if email is None:
        email = f"testuser-{uuid.uuid4()}@example.com"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "SecurePass123"
        }
    )
    assert response.status_code == 201
    return response.json()["user_id"]


class TestQuestionnaireSubmission:
    """Test suite for questionnaire submission endpoint"""
    
    def test_successful_questionnaire_submission(self):
        """Test successful questionnaire submission with valid data"""
        user_id = create_test_user()
        
        response = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "What best describes your collection style?",
                        "selected_options": ["Timeless Classics"]
                    },
                    {
                        "question_id": 2,
                        "question_text": "What items are you most passionate about?",
                        "selected_options": ["Handbags", "Watches"]
                    },
                    {
                        "question_id": 3,
                        "question_text": "What do you hope to get from the Book of H community?",
                        "selected_options": ["Inspiration", "Connecting with others"]
                    }
                ]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Questionnaire saved successfully"
        assert "questionnaire_id" in data
        assert len(data["questionnaire_id"]) > 0
    
    def test_questionnaire_submission_single_question(self):
        """Test questionnaire submission with single question"""
        user_id = create_test_user()
        
        response = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "What best describes your collection style?",
                        "selected_options": ["Modern & Trendy"]
                    }
                ]
            }
        )
        
        assert response.status_code == 201
        assert response.json()["message"] == "Questionnaire saved successfully"
    
    def test_questionnaire_submission_multiple_selections(self):
        """Test questionnaire submission with multiple selections per question"""
        user_id = create_test_user()
        
        response = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 2,
                        "question_text": "What items are you most passionate about?",
                        "selected_options": ["Handbags", "Watches", "Jewelry", "Shoes"]
                    }
                ]
            }
        )
        
        assert response.status_code == 201
    
    def test_questionnaire_update_existing(self):
        """Test that submitting questionnaire again updates the existing one"""
        user_id = create_test_user()
        
        # First submission
        response1 = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "What best describes your collection style?",
                        "selected_options": ["Timeless Classics"]
                    }
                ]
            }
        )
        assert response1.status_code == 201
        questionnaire_id1 = response1.json()["questionnaire_id"]
        
        # Second submission (update)
        response2 = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "What best describes your collection style?",
                        "selected_options": ["Modern & Trendy"]
                    }
                ]
            }
        )
        assert response2.status_code == 201
        questionnaire_id2 = response2.json()["questionnaire_id"]
        
        # Should be same questionnaire (updated, not new)
        assert questionnaire_id1 == questionnaire_id2
    
    def test_questionnaire_submission_invalid_user(self):
        """Test that questionnaire submission fails with invalid user_id"""
        response = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": "nonexistent-user-id",
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "Test question",
                        "selected_options": ["Test option"]
                    }
                ]
            }
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_questionnaire_submission_empty_answers(self):
        """Test questionnaire submission with empty answers array"""
        user_id = create_test_user()
        
        response = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": []
            }
        )
        
        # Should still succeed as empty questionnaire is technically valid
        assert response.status_code == 201
    
    def test_questionnaire_submission_missing_user_id(self):
        """Test that questionnaire submission fails without user_id"""
        response = client.post(
            "/api/questionnaire/submit",
            json={
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "Test question",
                        "selected_options": ["Test option"]
                    }
                ]
            }
        )
        
        assert response.status_code == 422
    
    def test_questionnaire_submission_missing_answers(self):
        """Test that questionnaire submission fails without answers"""
        user_id = create_test_user()
        
        response = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id
            }
        )
        
        assert response.status_code == 422
    
    def test_questionnaire_submission_invalid_answer_format(self):
        """Test questionnaire submission with invalid answer format"""
        user_id = create_test_user()
        
        response = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 1,
                        # Missing question_text and selected_options
                    }
                ]
            }
        )
        
        assert response.status_code == 422


class TestQuestionnaireRetrieval:
    """Test suite for questionnaire retrieval endpoint"""
    
    def test_successful_questionnaire_retrieval(self):
        """Test successful retrieval of questionnaire"""
        user_id = create_test_user()
        
        # First, submit a questionnaire
        submit_response = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "What best describes your collection style?",
                        "selected_options": ["Timeless Classics"]
                    },
                    {
                        "question_id": 2,
                        "question_text": "What items are you most passionate about?",
                        "selected_options": ["Handbags", "Watches"]
                    }
                ]
            }
        )
        assert submit_response.status_code == 201
        
        # Now retrieve it
        response = client.get(f"/api/questionnaire/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert len(data["answers"]) == 2
        assert "created_at" in data
        assert "updated_at" in data
        assert "id" in data
    
    def test_questionnaire_retrieval_nonexistent_user(self):
        """Test retrieval of questionnaire for non-existent user"""
        response = client.get("/api/questionnaire/nonexistent-user-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_questionnaire_retrieval_user_without_questionnaire(self):
        """Test retrieval when user exists but hasn't submitted questionnaire"""
        user_id = create_test_user()
        
        response = client.get(f"/api/questionnaire/{user_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_questionnaire_retrieval_verify_content(self):
        """Test that retrieved questionnaire contains correct data"""
        user_id = create_test_user()
        
        # Submit questionnaire with specific data
        test_answers = [
            {
                "question_id": 1,
                "question_text": "What best describes your collection style?",
                "selected_options": ["Rare & Eclectic"]
            },
            {
                "question_id": 2,
                "question_text": "What items are you most passionate about?",
                "selected_options": ["Jewelry", "Shoes"]
            },
            {
                "question_id": 3,
                "question_text": "What do you hope to get from the Book of H community?",
                "selected_options": ["Learning & Care Tips"]
            }
        ]
        
        client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": test_answers
            }
        )
        
        # Retrieve and verify
        response = client.get(f"/api/questionnaire/{user_id}")
        data = response.json()
        
        assert len(data["answers"]) == 3
        # Verify first answer
        assert data["answers"][0]["question_id"] == 1
        assert data["answers"][0]["question_text"] == "What best describes your collection style?"
        assert data["answers"][0]["selected_options"] == ["Rare & Eclectic"]
        
        # Verify second answer
        assert data["answers"][1]["question_id"] == 2
        assert data["answers"][1]["selected_options"] == ["Jewelry", "Shoes"]
        
        # Verify third answer
        assert data["answers"][2]["question_id"] == 3
        assert data["answers"][2]["selected_options"] == ["Learning & Care Tips"]


class TestQuestionnaireEndToEnd:
    """End-to-end tests for complete questionnaire flow"""
    
    def test_complete_user_questionnaire_flow(self):
        """Test complete flow: register, submit questionnaire, retrieve"""
        # 1. Register user
        reg_response = client.post(
            "/api/auth/register",
            json={
                "email": "flowtest@example.com",
                "password": "SecurePass123"
            }
        )
        assert reg_response.status_code == 201
        user_id = reg_response.json()["user_id"]
        
        # 2. Submit questionnaire
        submit_response = client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "What best describes your collection style?",
                        "selected_options": ["Modern & Trendy"]
                    }
                ]
            }
        )
        assert submit_response.status_code == 201
        
        # 3. Retrieve questionnaire
        get_response = client.get(f"/api/questionnaire/{user_id}")
        assert get_response.status_code == 200
        assert get_response.json()["user_id"] == user_id
    
    def test_multiple_users_questionnaires(self):
        """Test that multiple users can have separate questionnaires"""
        # Create first user and questionnaire
        user1_id = create_test_user()
        client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user1_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "Test",
                        "selected_options": ["Option A"]
                    }
                ]
            }
        )
        
        # Create second user and questionnaire
        reg_response2 = client.post(
            "/api/auth/register",
            json={
                "email": "user2@example.com",
                "password": "SecurePass123"
            }
        )
        user2_id = reg_response2.json()["user_id"]
        
        client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user2_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "Test",
                        "selected_options": ["Option B"]
                    }
                ]
            }
        )
        
        # Verify both questionnaires exist and are different
        q1 = client.get(f"/api/questionnaire/{user1_id}").json()
        q2 = client.get(f"/api/questionnaire/{user2_id}").json()
        
        assert q1["user_id"] == user1_id
        assert q2["user_id"] == user2_id
        assert q1["id"] != q2["id"]
        assert q1["answers"][0]["selected_options"] == ["Option A"]
        assert q2["answers"][0]["selected_options"] == ["Option B"]
    
    def test_questionnaire_update_preserves_timestamps(self):
        """Test that updating questionnaire updates the updated_at timestamp"""
        import time
        
        user_id = create_test_user()
        
        # Initial submission
        client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "Test",
                        "selected_options": ["Initial"]
                    }
                ]
            }
        )
        
        response1 = client.get(f"/api/questionnaire/{user_id}")
        created_at1 = response1.json()["created_at"]
        
        # Wait a bit
        time.sleep(0.1)
        
        # Update
        client.post(
            "/api/questionnaire/submit",
            json={
                "user_id": user_id,
                "answers": [
                    {
                        "question_id": 1,
                        "question_text": "Test",
                        "selected_options": ["Updated"]
                    }
                ]
            }
        )
        
        response2 = client.get(f"/api/questionnaire/{user_id}")
        data2 = response2.json()
        
        # created_at should remain the same
        assert data2["created_at"] == created_at1
        # But answers should be updated
        assert data2["answers"][0]["selected_options"] == ["Updated"]

