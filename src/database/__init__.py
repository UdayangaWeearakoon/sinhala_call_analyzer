import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from src.database.models import Call, DailyAggregate

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "sinhala_call_analytics")

client: AsyncIOMotorClient = None


def build_connection_string(uri: str, db_name: str) -> str:
    parsed = urlparse(uri)
    if parsed.path and parsed.path not in ("", "/"):
        return uri
    return urlunparse(parsed._replace(path=f"/{db_name}"))


async def init_db():
    global client
    client = AsyncIOMotorClient(build_connection_string(MONGODB_URI, DB_NAME))
    await init_beanie(
        connection_string=build_connection_string(MONGODB_URI, DB_NAME),
        document_models=[Call, DailyAggregate],
    )
    print(f"Database initialized: {DB_NAME}")


async def close_db():
    global client
    if client:
        client.close()
        print("Database connection closed.")