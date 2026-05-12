from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.database import init_db, close_db
from src.database.repository import (
    create_call,
    get_calls,
    get_call_by_id,
    get_overview_stats,
    get_category_trend,
    get_top_categories,
    update_daily_aggregate,
    refresh_all_daily_aggregates,
)
from src.database.schemas import (
    CallCreate,
    CallResponse,
    CallListResponse,
    OverviewResponse,
    CategoryTrendResponse,
)
from src.inference import CallAnalyticsPredictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        app.state.predictor = CallAnalyticsPredictor()
    except Exception:
        print("Warning: ML models not loaded. Inference will be unavailable.")
        app.state.predictor = None
    yield
    await close_db()


app = FastAPI(
    title="Sinhala Call Analytics API",
    description="API for analyzing Sinhala customer call transcripts",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/calls", response_model=CallResponse)
async def ingest_call(call: CallCreate):
    call_dict = call.model_dump()
    if not call_dict.get("category") or not call_dict.get("sentiment"):
        predictor = app.state.predictor
        if predictor is None:
            raise HTTPException(status_code=503, detail="ML models not loaded")
        try:
            result = predictor.predict(call_dict["transcript"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")
        call_dict["category"] = result["category"]
        call_dict["sentiment"] = result["sentiment"]
        call_dict["category_confidence"] = result["category_confidence"]
        call_dict["sentiment_confidence"] = result["sentiment_confidence"]

    db_call = await create_call(call_dict)
    await update_daily_aggregate(db_call.timestamp)
    return db_call


@app.get("/api/calls", response_model=CallListResponse)
async def list_calls(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
):
    skip = (page - 1) * page_size
    calls, total = await get_calls(
        skip=skip,
        limit=page_size,
        date_from=date_from,
        date_to=date_to,
        category=category,
        sentiment=sentiment,
    )
    return CallListResponse(calls=calls, total=total, page=page, page_size=page_size)


@app.get("/api/calls/{call_id}", response_model=CallResponse)
async def get_call(call_id: str):
    call = await get_call_by_id(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@app.get("/api/analytics/overview", response_model=OverviewResponse)
async def overview():
    return await get_overview_stats()


@app.get("/api/analytics/category-trend")
async def category_trend(days: int = Query(365, ge=1, le=3650)):
    return await get_category_trend(days=days)


@app.get("/api/analytics/top-categories")
async def top_categories(limit: int = Query(10, ge=1, le=50)):
    return await get_top_categories(limit=limit)


@app.post("/api/analytics/refresh-daily")
async def refresh_daily():
    count = await refresh_all_daily_aggregates()
    return {"message": f"Refreshed {count} daily aggregate records"}