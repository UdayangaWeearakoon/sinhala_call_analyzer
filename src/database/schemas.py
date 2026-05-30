from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CallCreate(BaseModel):
    transcript: str
    filename: Optional[str] = None
    source_type: Optional[str] = None
    category: Optional[str] = None
    sentiment: Optional[str] = None
    category_confidence: Optional[float] = None
    sentiment_confidence: Optional[float] = None
    customer_phone: Optional[str] = None
    call_duration: Optional[int] = None
    resolved: Optional[bool] = False
    notes: Optional[str] = None
    uploaded_at: Optional[datetime] = None


class CallResponse(BaseModel):
    id: int
    transcript: str
    filename: Optional[str] = None
    source_type: Optional[str] = None
    category: str
    sentiment: str
    category_confidence: float
    sentiment_confidence: float
    uploaded_at: Optional[datetime]
    timestamp: datetime
    call_duration: Optional[int] = None
    customer_phone: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[int] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class CallListResponse(BaseModel):
    calls: list[CallResponse]
    total: int
    page: int
    page_size: int


class OverviewResponse(BaseModel):
    total_calls_today: int
    total_calls_yesterday: int
    total_calls_this_month: int
    resolution_rate: float
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    category_distribution: dict[str, int]
    sentiment_distribution: dict[str, int]
    sentiment_trend: list[dict]


class CategoryTrendResponse(BaseModel):
    category: str
    date: str
    count: int