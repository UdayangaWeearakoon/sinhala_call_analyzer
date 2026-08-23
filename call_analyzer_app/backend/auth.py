import os
from datetime import datetime, timedelta, timezone

import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def verify_credentials(username: str, password: str) -> bool:
    valid_user = os.getenv("ADMIN_USERNAME", "")
    valid_pass = os.getenv("ADMIN_PASSWORD", "")
    return username == valid_user and password == valid_pass

def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    username = payload.get("sub")
    if not username:
        raise ValueError("Invalid token payload")
    return username