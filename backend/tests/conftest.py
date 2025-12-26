"""
Pytest configuration and fixtures for LANCH system tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import Usuario
from utils.security import get_password_hash


# Test database configuration
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user for testing"""
    user = Usuario(
        username="testadmin",
        password_hash=get_password_hash("TestAdmin@123"),
        nome="Test Administrator",
        perfil="ADMIN",
        ativo=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client, admin_user):
    """Get authentication headers for authorized requests"""
    response = client.post("/auth/login", json={
        "username": "testadmin",
        "password": "TestAdmin@123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def atendente_user(db_session):
    """Create an atendente user for testing"""
    user = Usuario(
        username="testatendente",
        password_hash=get_password_hash("TestAtend@123"),
        nome="Test Atendente",
        perfil="ATENDENTE",
        ativo=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def cozinha_user(db_session):
    """Create a cozinha user for testing"""
    user = Usuario(
        username="testcozinha",
        password_hash=get_password_hash("TestCoz@123"),
        nome="Test Cozinha",
        perfil="COZINHA",
        ativo=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
