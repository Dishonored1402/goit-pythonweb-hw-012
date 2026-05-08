from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class ContactBase(BaseModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: EmailStr
    phone_number: str = Field(max_length=20)
    birthday: date
    additional_data: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    birthday: Optional[date] = None
    additional_data: Optional[str] = None

class ContactResponse(ContactBase):
    id: int

    class Config:
        from_attributes = True

class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=12)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar: str

    class Config:
        from_attributes = True

class TokenModel(BaseModel): 
    access_token: str
    refresh_token: str
    token_type: str = "bearer"