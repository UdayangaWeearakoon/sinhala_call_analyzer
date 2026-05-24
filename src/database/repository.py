from datetime import datetime, timedelta, timezone
from typing import Optional
from bson import ObjectId
import src.database as db
from src.database.models import Call, DailyAggregate


NEGATIVE_SENTIMENTS = ["Negative", "Very Negative"]


def _calls_col():
    return db.client[db.DB_NAME]["calls"]


def _daily_col():
    return db.client[db.DB_NAME]["daily_aggregates"]


async def create_call(call_data: dict) -> Call:
    call = Call(**call_data)
    await call.insert()
    return call


async def find_duplicate_call(
    transcript_hash: str,
    transcript: str,
    source_file_name: Optional[str] = None,
) -> Optional[Call]:
    conditions = [
        {"transcript_hash": transcript_hash},
        {"transcript": transcript},
    ]

    if source_file_name:
        conditions.append({"source_file_name": source_file_name})

    doc = await _calls_col().find_one({"$or": conditions})
    return Call.model_validate(doc) if doc else None


async def get_calls(
    skip: int = 0,
    limit: int = 50,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
) -> tuple[list[Call], int]:
    filters = {}

    if date_from or date_to:
        ts_filter = {}
        if date_from:
            ts_filter["$gte"] = date_from
        if date_to:
            ts_filter["$lte"] = date_to
        filters["timestamp"] = ts_filter

    if category:
        filters["category"] = category

    if sentiment:
        filters["sentiment"] = sentiment

    total = await _calls_col().count_documents(filters)
    cursor = _calls_col().find(filters).sort("timestamp", -1).skip(skip).limit(limit)
    docs = await cursor.to_list()

    calls = [Call.model_validate(d) for d in docs]
    return calls, total


async def get_call_by_id(call_id: str) -> Optional[Call]:
    if not ObjectId.is_valid(call_id):
        return None

    doc = await _calls_col().find_one({"_id": ObjectId(call_id)})
    return Call.model_validate(doc) if doc else None


async def get_overview_stats() -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    month_start = today_start.replace(day=1)

    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_all": {"$sum": 1},
                "resolved": {"$sum": {"$cond": ["$resolved", 1, 0]}},
                "calls_today": {
                    "$sum": {"$cond": [{"$gte": ["$timestamp", today_start]}, 1, 0]}
                },
                "calls_yesterday": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$gte": ["$timestamp", yesterday_start]},
                                    {"$lt": ["$timestamp", today_start]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
                "calls_this_month": {
                    "$sum": {"$cond": [{"$gte": ["$timestamp", month_start]}, 1, 0]}
                },
            }
        }
    ]

    cursor = await _calls_col().aggregate(pipeline)
    stats = await cursor.to_list()
    agg = stats[0] if stats else {}
    total_all = agg.get("total_all", 0)

    sentiment_cursor = await _calls_col().aggregate([
        {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
    ])
    sentiment_counts_raw = await sentiment_cursor.to_list()
    sentiment_map = {r["_id"]: r["count"] for r in sentiment_counts_raw}

    positive = sentiment_map.get("Positive", 0)
    neutral = sentiment_map.get("Neutral", 0)
    negative = sum(sentiment_map.get(s, 0) for s in NEGATIVE_SENTIMENTS)

    category_cursor = await _calls_col().aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ])
    category_raw = await category_cursor.to_list()
    category_dist = {r["_id"]: r["count"] for r in category_raw}

    trend_cursor = await _calls_col().aggregate([
        {"$match": {"timestamp": {"$gte": today_start - timedelta(days=30)}}},
        {
            "$group": {
                "_id": {
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp",
                        }
                    },
                    "sentiment": "$sentiment",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.date": 1}},
    ])
    sentiment_trend_raw = await trend_cursor.to_list()

    all_sentiments = {r["_id"]["sentiment"] for r in sentiment_trend_raw}
    trend_map = {}

    for r in sentiment_trend_raw:
        d = r["_id"]["date"]
        sent = r["_id"]["sentiment"]
        count = r["count"]

        if d not in trend_map:
            trend_map[d] = {"date": d}
            for s in all_sentiments:
                trend_map[d][s] = 0

        trend_map[d][sent] = count

    return {
        "total_calls_today": agg.get("calls_today", 0),
        "total_calls_yesterday": agg.get("calls_yesterday", 0),
        "total_calls_this_month": agg.get("calls_this_month", 0),
        "resolution_rate": round(
            (agg.get("resolved", 0) / total_all * 100) if total_all > 0 else 0,
            1,
        ),
        "positive_percentage": round(
            (positive / total_all * 100) if total_all > 0 else 0,
            1,
        ),
        "negative_percentage": round(
            (negative / total_all * 100) if total_all > 0 else 0,
            1,
        ),
        "neutral_percentage": round(
            (neutral / total_all * 100) if total_all > 0 else 0,
            1,
        ),
        "category_distribution": dict(sorted(category_dist.items(), key=lambda x: -x[1])),
        "sentiment_distribution": dict(sorted(sentiment_map.items(), key=lambda x: -x[1])),
        "sentiment_trend": sorted(trend_map.values(), key=lambda x: x["date"]),
    }


async def get_category_trend(days: int = 365) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    cursor = await _calls_col().aggregate([
        {"$match": {"timestamp": {"$gte": cutoff}}},
        {
            "$group": {
                "_id": {
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp",
                        }
                    },
                    "category": "$category",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.date": 1}},
    ])
    rows = await cursor.to_list()

    return [
        {
            "category": r["_id"]["category"],
            "date": r["_id"]["date"],
            "count": r["count"],
        }
        for r in rows
    ]


async def get_top_categories(limit: int = 10) -> list[dict]:
    cursor = await _calls_col().aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ])
    rows = await cursor.to_list()

    return [{"category": r["_id"], "count": r["count"]} for r in rows]


async def update_daily_aggregate(day: datetime) -> DailyAggregate:
    day_date = day.replace(hour=0, minute=0, second=0, microsecond=0)
    next_day = day_date + timedelta(days=1)

    cursor = await _calls_col().aggregate([
        {"$match": {"timestamp": {"$gte": day_date, "$lt": next_day}}},
        {
            "$group": {
                "_id": None,
                "total_calls": {"$sum": 1},
                "resolved_count": {"$sum": {"$cond": ["$resolved", 1, 0]}},
                "positive_count": {
                    "$sum": {"$cond": [{"$eq": ["$sentiment", "Positive"]}, 1, 0]}
                },
                "negative_count": {
                    "$sum": {"$cond": [{"$in": ["$sentiment", NEGATIVE_SENTIMENTS]}, 1, 0]}
                },
                "neutral_count": {
                    "$sum": {"$cond": [{"$eq": ["$sentiment", "Neutral"]}, 1, 0]}
                },
            }
        },
    ])
    stats = await cursor.to_list()

    top_cursor = await _calls_col().aggregate([
        {"$match": {"timestamp": {"$gte": day_date, "$lt": next_day}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1},
    ])
    top_raw = await top_cursor.to_list()
    top_category = top_raw[0]["_id"] if top_raw else None

    existing_doc = await _daily_col().find_one({"date": day_date})
    s = stats[0] if stats else {}

    if existing_doc:
        await _daily_col().update_one(
            {"_id": existing_doc["_id"]},
            {
                "$set": {
                    "total_calls": s.get("total_calls", 0),
                    "resolved_count": s.get("resolved_count", 0),
                    "positive_count": s.get("positive_count", 0),
                    "negative_count": s.get("negative_count", 0),
                    "neutral_count": s.get("neutral_count", 0),
                    "top_category": top_category,
                }
            },
        )

        existing_doc = await _daily_col().find_one({"_id": existing_doc["_id"]})
        return DailyAggregate.model_validate(existing_doc)

    aggregate = DailyAggregate(
        date=day_date,
        total_calls=s.get("total_calls", 0),
        resolved_count=s.get("resolved_count", 0),
        positive_count=s.get("positive_count", 0),
        negative_count=s.get("negative_count", 0),
        neutral_count=s.get("neutral_count", 0),
        top_category=top_category,
    )

    await aggregate.insert()
    return aggregate


async def refresh_all_daily_aggregates() -> int:
    cursor = await _calls_col().aggregate([
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$timestamp",
                    }
                }
            }
        },
    ])
    dates = await cursor.to_list()

    count = 0

    for r in dates:
        day = datetime.strptime(r["_id"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        await update_daily_aggregate(day)
        count += 1

    return count
