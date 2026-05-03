from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    team = Column(String(50), nullable=True)
    joined_date = Column(DateTime, default=utcnow)

    calls = relationship("Call", back_populates="agent")


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transcript = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    sentiment = Column(String(50), nullable=False)
    category_confidence = Column(Float, nullable=False)
    sentiment_confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=utcnow, index=True)
    call_duration = Column(Integer, nullable=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    resolved = Column(Boolean, default=False)
    resolution_time = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    agent = relationship("Agent", back_populates="calls")


class DailyAggregate(Base):
    __tablename__ = "daily_aggregates"
    __table_args__ = (UniqueConstraint("date", name="uq_daily_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    total_calls = Column(Integer, default=0)
    resolved_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    top_category = Column(String(100), nullable=True)
