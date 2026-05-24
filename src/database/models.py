from datetime import datetime, timezone
from typing import Optional
from beanie import Document
from pydantic import Field


def utcnow():
    return datetime.now(timezone.utc)


class Call(Document):
    transcript: str
    source_file_name: Optional[str] = None
    transcript_hash: Optional[str] = None
    category: str
    sentiment: str
    category_confidence: float
    sentiment_confidence: float
    timestamp: datetime = Field(default_factory=utcnow)
    call_duration: Optional[int] = None
    customer_phone: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[int] = None
    notes: Optional[str] = None

    class Settings:
        name = "calls"
        indexes = [
            "timestamp",
            "category",
            "sentiment",
            "source_file_name",
            "transcript_hash",
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
