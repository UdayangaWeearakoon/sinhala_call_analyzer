from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field
from pymongo import IndexModel


def utcnow():
    return datetime.now(timezone.utc)


class Call(Document):
    transcript: str
    category: str
    sentiment: str
    category_confidence: float
    sentiment_confidence: float
    filename: Optional[str] = None
    file_hash: Optional[str] = None
    source_type: str = "text_input"
    uploaded_at: datetime = Field(default_factory=utcnow)
    timestamp: datetime = Field(default_factory=utcnow)
    call_duration: Optional[int] = None
    customer_phone: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[int] = None
    notes: Optional[str] = None

    class Settings:
        name = "calls"
        indexes = [
            IndexModel([("file_hash", 1)], unique=True, sparse=True),
            "timestamp",
            "category",
            "sentiment",
        ]


class DailyAggregate(Document):
    date: datetime
    total_calls: int = 0
    resolved_count: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    top_category: Optional[str] = None

    class Settings:
        name = "daily_aggregates"
        indexes = [
            "date",
        ]