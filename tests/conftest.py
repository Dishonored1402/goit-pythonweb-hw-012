import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from src.database.db import Base, get_db
from src.database.models import User
from src.services.auth import auth_service

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

@pytest.fixture(scope="module")
def user(session):
    unique_email = "test_user@example.com"
    user = session.query(User).filter(User.email == unique_email).first()
    if not user:
        hashed_password = auth_service.get_password_hash("password123")
        user = User(
            username="testuser",
            email=unique_email,
            password=hashed_password,
            confirmed=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

@pytest.fixture(scope="module")
def token(user):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(auth_service.create_access_token(data={"sub": user.email}))