import pickle
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users


class Auth:
    """
    Class for handling authentication operations, including password hashing,
    token creation, and user caching with Redis.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = os.getenv("SECRET_KEY", "secret_key")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")
    
    cache = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=6379,
        db=0
    )

    def verify_password(self, plain_password, hashed_password):
        """Verifies if the plain password matches the hashed password."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """Generates a bcrypt hash from a plain password."""
        return self.pwd_context.hash(password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """Creates a new Access Token."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + (timedelta(seconds=expires_delta) if expires_delta else timedelta(minutes=15))
        to_encode.update({"iat": now, "exp": expire, "scope": "access_token"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """Creates a new Refresh Token."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + (timedelta(seconds=expires_delta) if expires_delta else timedelta(days=7))
        to_encode.update({"iat": now, "exp": expire, "scope": "refresh_token"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def create_email_token(self, data: dict):
        """Creates a token for email verification."""
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=1)
        to_encode.update({"iat": now, "exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    async def get_email_from_token(self, token: str):
        """Decodes the email from a given token."""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload["sub"]
        except JWTError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid token")

    def create_reset_token(self, email: str):
        """Creates a token for password reset."""
        to_encode = {"sub": email, "scope": "reset_password"}
        now = datetime.now(timezone.utc)
        expire = now + timedelta(hours=1)
        to_encode.update({"iat": now, "exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    async def get_email_from_reset_token(self, token: str):
        """Validates and retrieves email from a password reset token."""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("scope") == "reset_password":
                return payload["sub"]
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token scope")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid token")

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        Retrieves the current user from Redis cache or database.
        Implements Redis caching to improve performance.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("scope") == "access_token":
                email = payload.get("sub")
                if email is None: raise credentials_exception
            else: raise credentials_exception
        except JWTError: raise credentials_exception

        user_cache_key = f"user:{email}"
        cached_user = self.cache.get(user_cache_key)

        if cached_user:
            user = pickle.loads(cached_user)
        else:
            user = await repository_users.get_user_by_email(email, db)
            if user is None: raise credentials_exception
            self.cache.setex(user_cache_key, 900, pickle.dumps(user))

        return user

auth_service = Auth()