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