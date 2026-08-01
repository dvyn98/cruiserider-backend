from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(
        data:dict,
        expires_delta: Optional[timedelta]= None
) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )    

    to_encode.update({
        "exp": expire,
        "type": "access"
    })    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
        data : dict,
        expires_delta: Optional[timedelta]=None
) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)


    to_encode.update({
        "exp": expire,
        "type":"refresh"
    })        
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_token(token : str) -> dict:

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise ValueError("Invalid or Expired Token")