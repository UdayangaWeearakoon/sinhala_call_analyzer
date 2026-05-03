from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CallCreate(BaseModel):
    transcript: str
    category: Optional[str] = None
    sentiment: Optional[str] = None
    category_confidence: Optional[float] = None
    sentiment_confidence: Optional[float] = None
    agent_id: Optional[int] = None
    customer_phone: Optional[str] = None
    call_duration: Optional[int] = None
    resolved: Optional[bool] = False
    notes: Optional[str] = None


class CallResponse(BaseModel):
    id: int
    transcript: str
    category: Optional[str]
    sentiment: Optional[str]
    category_confidence: Optional[float]
    sentiment_confidence: Optional[float]
    timestamp: datetime
    call_duration: Optional[int]
    agent_id: Optional[int]
    customer_phone: Optional[str]
    resolved: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


class CallListResponse(BaseModel):
    calls: list[CallResponse]
    total: int
    page: int
    page_size: int


class AgentCreate(BaseModel):
    name: str
    team: Optional[str] = None


class AgentResponse(BaseModel):
    id: int
    name: str
    team: Optional[str]

    class Config:
        from_attributes = True


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


class AgentPerformanceResponse(BaseModel):
    agent_id: int
    agent_name: str
    team: Optional[str]
    total_calls: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: float
    negative_percentage: float
    resolved_count: int
    resolution_rate: float


class CategoryTrendResponse(BaseModel):
    category: str
    date: str
    count: int
