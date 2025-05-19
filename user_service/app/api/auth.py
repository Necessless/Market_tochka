from fastapi import Depends, HTTPException, Header
import jwt
from config import settings
from passlib.context import CryptContext

SECRET_KEY = settings.hash.secret
ALGORITHM = settings.hash.algorithm

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(data: dict) -> str:
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
