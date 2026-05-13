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
    return current_user

@router.patch('/avatar', response_model=UserResponse, dependencies=[Depends(allowed_get_avatar)])
async def update_avatar_user(file: UploadFile = File(), 
                             current_user: User = Depends(auth_service.get_current_user), 
                             db: Session = Depends(get_db)):
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
async def forgot_password(
    body: RequestEmail,
    db: Session = Depends(get_db)
):
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
    email = await auth_service.get_email_from_reset_token(token)
    user = await repository_users.get_user_by_email(email, db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")

    new_password_hash = auth_service.get_password_hash(body.new_password)
    await repository_users.update_password(user, new_password_hash, db)

    return {"message": "Password updated successfully"}