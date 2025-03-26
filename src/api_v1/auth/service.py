import hashlib
from passlib.context import CryptContext
from core.config import settings

private_salt = settings.hash.salt
pwd_hash = CryptContext(schemes=['bcrypt'], deprecated='auto')

def generate_api_key(user_id: int) -> str:
    try:
        key = str(user_id) + private_salt
        generated_key = hashlib.sha256(key.encode()).hexdigest()
        return generated_key
    except Exception as e:
        raise e

def hash_api_key(api_key):
    return pwd_hash.hash(api_key)


def verify_hashed_key(api_key, hashed_api_key):
    return pwd_hash.verify(api_key,hashed_api_key)