import os
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import cloudinary
import cloudinary.uploader

from src.database.db import get_db
from src.database.models import User, Role
from src.schemas import UserSchema, UserResponse, TokenModel, RequestEmail, ResetPasswordModel
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email
from src.services.roles import RoleChecker
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix='/auth', tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

allowed_get_avatar = RoleChecker([Role.admin])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserSchema, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """Register a new user and send an email confirmation message.

    :param body: User registration data.
    :param background_tasks: FastAPI background task manager.
    :param request: Current HTTP request used to build the host URL.
    :param db: Database session.
    :return: Created user object.
    :raises HTTPException: If a user with the same email already exists.
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")

    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)

    host = str(request.base_url)
    background_tasks.add_task(send_email, new_user.email, new_user.username, host)

    return new_user


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate a confirmed user and return JWT access and refresh tokens.

    :param body: OAuth2 form with username as email and password.
    :param db: Database session.
    :return: Access token, refresh token and token type.
    :raises HTTPException: If email, password or confirmation status is invalid.
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")

    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")

    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """Confirm a user's email address using an email verification token.

    :param token: Email confirmation JWT token.
    :param db: Database session.
    :return: Confirmation result message.
    :raises HTTPException: If the token does not match an existing user.
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed successfully"}


@router.get("/me", response_model=UserResponse)
@limiter.limit("5/minute")
async def read_users_me(request: Request, current_user: User = Depends(auth_service.get_current_user)):
    """Return the current authenticated user profile.

    The endpoint is protected by JWT authentication and rate limiting.

    :param request: Current HTTP request required by SlowAPI limiter.
    :param current_user: User resolved from the JWT token.
    :return: Current user profile.
    """
    return current_user


@router.patch('/avatar', response_model=UserResponse, dependencies=[Depends(allowed_get_avatar)])
async def update_avatar_user(file: UploadFile = File(),
                             current_user: User = Depends(auth_service.get_current_user),
                             db: Session = Depends(get_db)):
    """Update the current user's avatar in Cloudinary.

    This route is protected by role-based access control and is available only
    for users with the admin role.

    :param file: Uploaded avatar file.
    :param current_user: Current authenticated user.
    :param db: Database session.
    :return: Updated user object with a new avatar URL.
    """
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET'),
        secure=True
    )
    r = cloudinary.uploader.upload(file.file, public_id=f'Avatars/{current_user.username}', overwrite=True)
    src_url = cloudinary.CloudinaryImage(f'Avatars/{current_user.username}')\
                        .build_url(width=250, height=250, crop='fill', version=r.get('version'))
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    return user


@router.post("/forgot_password")
async def forgot_password(body: RequestEmail, db: Session = Depends(get_db)):
    """Create a password reset token for an existing user.

    For this homework project the reset token is returned in the response so it
    can be tested through Swagger or automated tests.

    :param body: User email for password reset.
    :param db: Database session.
    :return: Reset token for existing users or a generic message.
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user:
        reset_token = auth_service.create_reset_token(user.email)
        return {
            "message": "Use this token to reset password",
            "reset_token": reset_token
        }

    return {"message": "Check your email for a password reset link."}


@router.post("/reset_password/{token}")
async def reset_password(token: str, body: ResetPasswordModel, db: Session = Depends(get_db)):
    """Reset a user's password using a valid reset token.

    :param token: Password reset JWT token.
    :param body: New password data.
    :param db: Database session.
    :return: Password update result message.
    :raises HTTPException: If token is invalid or user does not exist.
    """
    email = await auth_service.get_email_from_reset_token(token)
    user = await repository_users.get_user_by_email(email, db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")

    new_password_hash = auth_service.get_password_hash(body.new_password)
    await repository_users.update_password(user, new_password_hash, db)

    return {"message": "Password updated successfully"}
