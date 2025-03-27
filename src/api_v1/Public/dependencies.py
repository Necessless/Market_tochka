from fastapi import HTTPException
from fastapi import Header


def api_key_header(authorization: str = Header(...)):
    if not authorization.startswith("TOKEN "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    return token