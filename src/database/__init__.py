import os
from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from beanie import init_beanie
from src.database.models import Call, DailyAggregate

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "sinhala_call_analytics")

client: AsyncMongoClient = None


async def init_db():
    global client
    client = AsyncMongoClient(MONGODB_URI)

    await init_beanie(
        database=client[DB_NAME],
        document_models=[Call, DailyAggregate],
    )

    print(f"Database initialized: {DB_NAME}")


async def close_db():
    global client
    if client:
        client.close()
        print("Database connection closed.")