from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(50), nullable=False)
    category_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sentiment_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    source_type: Mapped[str] = mapped_column(String(50), default="text_input")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    call_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_timestamp", "timestamp"),
        Index("idx_category", "category"),
        Index("idx_sentiment", "sentiment"),
    )


class DailyAggregate(Base):
    __tablename__ = "daily_aggregates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(DateTime, unique=True, nullable=False)
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    resolved_count: Mapped[int] = mapped_column(Integer, default=0)
    positive_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0)
    top_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        Index("idx_agg_date", "date"),
    )
