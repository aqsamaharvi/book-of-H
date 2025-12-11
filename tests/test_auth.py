import pytest
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


class TestUserRegistration:
    """Test suite for user registration endpoint"""
    
    def test_successful_registration(self):
        """Test successful user registration with valid data"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Account created successfully"
        assert "user_id" in data
        assert "email" in data
        assert data["email"] == "test@example.com"
    
    def test_duplicate_email_rejection(self):
        """Test that duplicate email addresses are rejected"""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123"
            }
        )
        
        # Second registration with same email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "DifferentPass456"
            }
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
    
    def test_invalid_email_format(self):
        """Test that invalid email formats are rejected"""
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@nodomain.com",
            "spaces in@email.com",
            "double@@domain.com"
        ]
        
        for invalid_email in invalid_emails:
            response = client.post(
                "/api/auth/register",
                json={
                    "email": invalid_email,
                    "password": "SecurePass123"
                }
            )
            assert response.status_code == 422, f"Failed for email: {invalid_email}"
    
    def test_password_too_short(self):
        """Test that passwords shorter than 8 characters are rejected"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "Short1"
            }
        )
        assert response.status_code == 422
        assert "at least 8 characters" in str(response.json()).lower()
    
    def test_password_missing_uppercase(self):
        """Test that passwords without uppercase letters are rejected"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "lowercase123"
            }
        )
        assert response.status_code == 422
        assert "uppercase" in str(response.json()).lower()
    
    def test_password_missing_lowercase(self):
        """Test that passwords without lowercase letters are rejected"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "UPPERCASE123"
            }
        )
        assert response.status_code == 422
        assert "lowercase" in str(response.json()).lower()
    
    def test_password_missing_number(self):
        """Test that passwords without numbers are rejected"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "NoNumbersHere"
            }
        )
        assert response.status_code == 422
        assert "number" in str(response.json()).lower()
    
    def test_valid_password_requirements(self):
        """Test that passwords meeting all requirements are accepted"""
        valid_passwords = [
            "SecurePass123",
            "MyP@ssw0rd",
            "Test1234Password",
            "ValidPass999"
        ]
        
        for i, password in enumerate(valid_passwords):
            response = client.post(
                "/api/auth/register",
                json={
                    "email": f"user{i}@example.com",
                    "password": password
                }
            )
            assert response.status_code == 201, f"Failed for password: {password}"
    
    def test_missing_email_field(self):
        """Test that missing email field is rejected"""
        response = client.post(
            "/api/auth/register",
            json={
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 422
    
    def test_missing_password_field(self):
        """Test that missing password field is rejected"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com"
            }
        )
        assert response.status_code == 422


class TestUserLogin:
    """Test suite for user login endpoint"""
    
    def test_successful_login(self):
        """Test successful login with valid credentials"""
        # First, register a user
        client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123"
            }
        )
        
        # Then login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_with_wrong_password(self):
        """Test that login fails with incorrect password"""
        # Register a user
        client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "password": "CorrectPass123"
            }
        )
        
        # Try to login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "email": "user@example.com",
                "password": "WrongPass123"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_with_nonexistent_email(self):
        """Test that login fails with non-existent email"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePass123"
            }
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_login_after_registration(self):
        """Test complete flow: register then login"""
        email = "fullflow@example.com"
        password = "SecurePass123"
        
        # Register
        reg_response = client.post(
            "/api/auth/register",
            json={"email": email, "password": password}
        )
        assert reg_response.status_code == 201
        
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={"email": email, "password": password}
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
    
    def test_login_case_sensitive_password(self):
        """Test that password is case-sensitive"""
        # Register
        client.post(
            "/api/auth/register",
            json={
                "email": "case@example.com",
                "password": "SecurePass123"
            }
        )
        
        # Try login with different case
        response = client.post(
            "/api/auth/login",
            json={
                "email": "case@example.com",
                "password": "securepass123"
            }
        )
        assert response.status_code == 401


class TestAPIHealth:
    """Test suite for health check endpoint"""
    
    def test_health_check(self):
        """Test that health check endpoint works"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_empty_request_body(self):
        """Test that empty request body is rejected"""
        response = client.post("/api/auth/register", json={})
        assert response.status_code == 422
    
    def test_extra_fields_ignored(self):
        """Test that extra fields in request are ignored"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "extra@example.com",
                "password": "SecurePass123",
                "extra_field": "should_be_ignored"
            }
        )
        assert response.status_code == 201
    
    def test_very_long_password(self):
        """Test that very long passwords are accepted"""
        long_password = "A1" + "a" * 100  # 102 character password
        response = client.post(
            "/api/auth/register",
            json={
                "email": "longpass@example.com",
                "password": long_password
            }
        )
        assert response.status_code == 201
    
    def test_email_with_special_characters(self):
        """Test emails with valid special characters"""
        valid_emails = [
            "user+tag@example.com",
            "user.name@example.com",
            "user_name@example.com"
        ]
        
        for i, email in enumerate(valid_emails):
            response = client.post(
                "/api/auth/register",
                json={
                    "email": email,
                    "password": f"SecurePass{i}23"
                }
            )
            assert response.status_code == 201, f"Failed for email: {email}"

