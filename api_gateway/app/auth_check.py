from fastapi import Depends, HTTPException, Header
from config import settings
import jwt
from httpx_helper import httpx_helper

SECRET_KEY = settings.hash.secret
ALGORITHM = settings.hash.algorithm


def api_key_header(authorization: str = Header(...)) -> tuple[str, str]:
    if not authorization.startswith("TOKEN "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        role = payload.get('role')
        return user_id, role
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authorization token")

    