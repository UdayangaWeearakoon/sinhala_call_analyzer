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

app = FastAPI(title="Call Analyzer API")