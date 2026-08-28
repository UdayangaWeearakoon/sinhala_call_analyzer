import logging
import os
from typing import Any

import mysql.connector
import mysql.connector.pooling
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

import auth

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO)
logging.getLogger("mysql.connector").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI(title="Call Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

DB_POOL_NAME = "call_analyzer_pool"
DB_POOL_SIZE = 5

pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name=DB_POOL_NAME,
    pool_size=DB_POOL_SIZE,
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "call_analyzer"),
)


def get_connection() -> mysql.connector.MySQLConnection:
    return pool.get_connection()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        return auth.decode_access_token(token)
    except auth.jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except (auth.jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")




# --- Auth models ---

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"    


# --- Auth endpoints ---

# --- Auth endpoints ---

@app.post("/api/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if not auth.verify_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # මේ පේළි 3 නිවැරදිව indent කර function එක ඇතුළට ගත යුතුයි
    token = auth.create_access_token(body.username)    
    logger.info("User '%s' logged in", body.username)
    return TokenResponse(access_token=token)




@app.get("/api/auth/me")
def get_me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}


# --- Protected endpoints ---

@app.get("/api/call-analytics")
def get_call_analytics(
    current_user: str = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
) -> dict[str, Any]:
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total, AVG(confidence) AS avg_conf FROM transcripts")
        agg = cursor.fetchone()
        total_calls = agg["total"]
        avg_confidence = round(agg["avg_conf"], 2) if agg.get("avg_conf") is not None else None

        cursor.execute(
            "SELECT category, COUNT(*) AS cnt FROM transcripts "
            
        )


    