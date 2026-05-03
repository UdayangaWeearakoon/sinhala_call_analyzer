from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db, init_db
from src.database.repository import (
    create_call,
    get_calls,
    get_call_by_id,
    get_agents,
    get_agent_by_name,
    create_agent,
    get_overview_stats,
    get_agent_performance,
    get_category_trend,
    get_top_categories,
)
from src.database.schemas import (
    CallCreate,
    CallResponse,
    CallListResponse,
    AgentCreate,
    AgentResponse,
    OverviewResponse,
    AgentPerformanceResponse,
    CategoryTrendResponse,
)
from src.inference import CallAnalyticsPredictor

app = FastAPI(
    title="Sinhala Call Analytics API",
    description="API for analyzing Sinhala customer call transcripts",
    version="1.0.0",
)

predictor = None


@app.on_event("startup")
def startup():
    init_db()
    global predictor
    try:
        predictor = CallAnalyticsPredictor()
    except Exception:
        print("Warning: ML models not loaded. Inference will be unavailable.")


@app.post("/api/calls", response_model=CallResponse)
def ingest_call(call: CallCreate, db: Session = Depends(get_db)):
    if not call.category or not call.sentiment:
        if predictor is None:
            raise HTTPException(status_code=503, detail="ML models not loaded")
        result = predictor.predict(call.transcript)
        call.category = result["category"]
        call.sentiment = result["sentiment"]
        call.category_confidence = result["category_confidence"]
        call.sentiment_confidence = result["sentiment_confidence"]

    db_call = create_call(db, call.model_dump())
    return db_call


@app.get("/api/calls", response_model=CallListResponse)
def list_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    agent_id: Optional[int] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    calls, total = get_calls(
        db,
        skip=skip,
        limit=page_size,
        date_from=date_from,
        date_to=date_to,
        agent_id=agent_id,
        category=category,
        sentiment=sentiment,
    )
    return CallListResponse(calls=calls, total=total, page=page, page_size=page_size)


@app.get("/api/calls/{call_id}", response_model=CallResponse)
def get_call(call_id: int, db: Session = Depends(get_db)):
    call = get_call_by_id(db, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@app.get("/api/analytics/overview", response_model=OverviewResponse)
def overview(db: Session = Depends(get_db)):
    return get_overview_stats(db)


@app.get("/api/analytics/agent-performance")
def agent_performance(db: Session = Depends(get_db)):
    return get_agent_performance(db)


@app.get("/api/analytics/category-trend")
def category_trend(days: int = Query(365, ge=1, le=3650), db: Session = Depends(get_db)):
    return get_category_trend(db, days=days)


@app.get("/api/analytics/top-categories")
def top_categories(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    return get_top_categories(db, limit=limit)


@app.post("/api/agents", response_model=AgentResponse)
def create_new_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    existing = get_agent_by_name(db, agent.name)
    if existing:
        raise HTTPException(status_code=400, detail="Agent already exists")
    return create_agent(db, agent.name, agent.team)


@app.get("/api/agents", response_model=list[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    return get_agents(db)
