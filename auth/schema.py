from typing import Optional
from pydantic import BaseModel, EmailStr
from pydantic import BaseModel


class GoogleAuthPayload(BaseModel):
    token: str


class User(BaseModel):
    username: str
    email: EmailStr
    password: str


class DisplayAccount(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_image: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class Login(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    email: str
    role: str


class TokenData(BaseModel):
    email: Optional[str] = None
    id: Optional[int]
