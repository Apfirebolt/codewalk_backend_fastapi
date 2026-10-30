from datetime import datetime, timedelta
from typing import Optional

from . import schema

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt as pyjwt


SECRET_KEY = "20a9bfa73de3f29b6b7a01d4fc84bb569f1b7e8ac7f83c77c62a603f2bf9f5ff"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException) -> schema.TokenData:
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        id: int = payload.get("id")
        if email is None:
            raise credentials_exception
        token_data = schema.TokenData(email=email, id=id)
        return token_data
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except pyjwt.PyJWTError:
        raise credentials_exception

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> schema.TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Authorization": "Bearer"}
    )
    if not credentials or not credentials.credentials:
        raise credentials_exception
    token = credentials.credentials
    return verify_token(token, credentials_exception)


def verify_token_simple(token: str) -> Optional[schema.TokenData]:
    """Verify token for WebSocket connections without raising exceptions"""
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        id: int = payload.get("id")
        if email is None:
            return None
        token_data = schema.TokenData(email=email, id=id)
        return token_data
    except Exception:
        return None
