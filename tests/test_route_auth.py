import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.db import Base, get_db
from main import app
from src.database.models import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)

# --- ТЕСТЫ ---

def test_signup_success(client):
    response = client.post(
        "/api/auth/signup",
        json={"username": "testuser", "email": "newuser@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "newuser@example.com"

def test_signup_duplicate_email(client):
    response = client.post(
        "/api/auth/signup",
        json={"username": "another", "email": "newuser@example.com", "password": "password123"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Account already exists"

def test_login_not_confirmed(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "newuser@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Email not confirmed"

def test_login_wrong_password(client, session):
    user = session.query(User).filter(User.email == "newuser@example.com").first()
    user.confirmed = True
    session.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": "newuser@example.com", "password": "wrong_password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password"

def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "newuser@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_read_users_me(client):
    login_response = client.post(
        "/api/auth/login",
        data={"username": "newuser@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "newuser@example.com"

def test_forgot_password(client):
    response = client.post(
        "/api/auth/forgot_password",
        json={"email": "newuser@example.com"}
    )
    assert response.status_code == 200
    assert "message" in response.json()