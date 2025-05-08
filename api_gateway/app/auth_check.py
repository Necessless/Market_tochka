from fastapi import HTTPException, Header
from config import settings
import jwt

SECRET_KEY = settings.hash.secret
ALGORITHM = settings.hash.algorithm

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