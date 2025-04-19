from fastapi import Depends, HTTPException, Header
import jwt
from .config import settings
from passlib.context import CryptContext

SECRET_KEY = settings.hash.secret
ALGORITHM = settings.hash.algorithm

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(data: dict) -> str:
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def api_key_header(authorization: str = Header(...)) -> str:
    if not authorization.startswith("TOKEN "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name = payload.get("name")
        return user_name
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authorization token")