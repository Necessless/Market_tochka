import hashlib
import hmac
import secrets
from core.config import settings

__salt = settings.hash.salt
SECRET_KEY = __salt.encode()

def generate_api_key():
    return "key-" + secrets.token_hex(16) 

def hash_api_key(api_key: str) -> str:
    """Хеш с помощью SHA-256"""
    return hmac.new(SECRET_KEY, api_key.encode(), hashlib.sha256).hexdigest()
