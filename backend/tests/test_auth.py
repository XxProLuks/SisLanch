"""
Tests for authentication endpoints
"""
import pytest
from fastapi import status


class TestLogin:
    """Test cases for login functionality"""
    
    def test_login_success(self, client, admin_user):
        """Test successful login with correct credentials"""
        response = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "TestAdmin@123"
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_username(self, client):
        """Test login with non-existent username"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "anypassword"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Usuário ou senha incorretos" in response.json()["detail"]
    
    def test_login_invalid_password(self, client, admin_user):
        """Test login with incorrect password"""
        response = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "wrongpassword"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_inactive_user(self, client, db_session, admin_user):
        """Test login with inactive user"""
        admin_user.ativo = False
        db_session.commit()
        
        response = client.post("/auth/login", json={
            "username": "testadmin",
            "password": "TestAdmin@123"
        })
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "desativado" in response.json()["detail"].lower()
    
    def test_login_missing_fields(self, client):
        """Test login with missing required fields"""
        response = client.post("/auth/login", json={
            "username": "testadmin"
        })
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetCurrentUser:
    """Test cases for getting current user info"""
    
    def test_get_current_user_success(self, client, auth_headers):
        """Test getting current user with valid token"""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "testadmin"
        assert data["perfil"] == "ADMIN"
        assert "password_hash" not in data
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without authentication"""
        response = client.get("/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer invalid_token"
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestChangePassword:
    """Test cases for password change"""
    
    def test_change_password_success(self, client, auth_headers):
        """Test successful password change"""
        response = client.post("/auth/change-password", 
            headers=auth_headers,
            json={
                "current_password": "TestAdmin@123",
                "new_password": "NewSecure@456"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "sucesso" in response.json()["message"].lower()
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change with wrong current password"""
        response = client.post("/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "WrongPassword@123",
                "new_password": "NewSecure@456"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "incorreta" in response.json()["detail"].lower()
    
    def test_change_password_weak_new_password(self, client, auth_headers):
        """Test password change with weak new password"""
        response = client.post("/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "TestAdmin@123",
                "new_password": "weak"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_change_password_same_as_current(self, client, auth_headers):
        """Test password change with same password"""
        response = client.post("/auth/change-password",
            headers=auth_headers,
            json={
                "current_password": "TestAdmin@123",
                "new_password": "TestAdmin@123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "igual" in response.json()["detail"].lower()


class TestRateLimiting:
    """Test cases for rate limiting on auth endpoints"""
    
    def test_login_rate_limit(self, client):
        """Test that rate limiting is applied to login attempts"""
        # Make 6 failed login attempts (limit is 5/minute)
        for i in range(6):
            response = client.post("/auth/login", json={
                "username": "testuser",
                "password": "wrongpass"
            })
            
            if i < 5:
                # First 5 should go through (may fail auth, but not rate limited)
                assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_429_TOO_MANY_REQUESTS]
            else:
                # 6th request should be rate limited
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
