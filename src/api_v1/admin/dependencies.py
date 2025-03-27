from api_v1.Public.schemas import UserBase
from fastapi import HTTPException, Header
from core.models.Users import AuthRole


def is_admin_user(user: UserBase) -> bool:
    if user.role != AuthRole.ADMIN:
        raise HTTPException(status_code=405, detail="Method is not allowed")
    return True
