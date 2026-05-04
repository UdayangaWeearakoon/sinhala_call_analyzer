from datetime import datetime, date, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.database.models import Call, Agent, DailyAggregate


def create_call(db: Session, call_data: dict) -> Call:
    db_call = Call(**call_data)
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    return db_call


def get_calls(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    agent_id: Optional[int] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
):
    query = db.query(Call)

    if date_from:
        query = query.filter(Call.timestamp >= date_from)
    if date_to:
        query = query.filter(Call.timestamp <= date_to)
    if agent_id:
        query = query.filter(Call.agent_id == agent_id)
    if category:
        query = query.filter(Call.category == category)
    if sentiment:
        query = query.filter(Call.sentiment == sentiment)

    total = query.count()
    calls = query.order_by(desc(Call.timestamp)).offset(skip).limit(limit).all()
    return calls, total


def get_call_by_id(db: Session, call_id: int) -> Optional[Call]:
    return db.query(Call).filter(Call.id == call_id).first()


def get_agents(db: Session):
    return db.query(Agent).all()


def get_agent_by_name(db: Session, name: str) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.name == name).first()


def create_agent(db: Session, name: str, team: Optional[str] = None) -> Agent:
    agent = Agent(name=name, team=team)
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def get_overview_stats(db: Session) -> dict:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    month_start = today.replace(day=1)

    calls_today = db.query(Call).filter(Call.timestamp >= today).count()
    calls_yesterday = db.query(Call).filter(
        Call.timestamp >= yesterday, Call.timestamp < today
    ).count()
    calls_this_month = db.query(Call).filter(Call.timestamp >= month_start).count()

    total_all = db.query(Call).count()
    resolved = db.query(Call).filter(Call.resolved == True).count()

    sentiment_counts = (
        db.query(Call.sentiment, func.count(Call.id))
        .group_by(Call.sentiment)
        .all()
    )
    sentiment_map = {s: c for s, c in sentiment_counts}

    positive = sentiment_map.get("Positive", 0)
    neutral = sentiment_map.get("Neutral", 0)
    negative = total_all - positive - neutral

    category_counts = (
        db.query(Call.category, func.count(Call.id))
        .group_by(Call.category)
        .all()
    )

    sentiment_trend = (
        db.query(
            func.date(Call.timestamp).label("date"),
            Call.sentiment,
            func.count(Call.id).label("count"),
        )
        .filter(Call.timestamp >= today - timedelta(days=30))
        .group_by(func.date(Call.timestamp), Call.sentiment)
        .order_by(func.date(Call.timestamp))
        .all()
    )

    all_sentiments = set(r[1] for r in sentiment_trend)
    trend_map = {}
    for d, sent, count in sentiment_trend:
        if str(d) not in trend_map:
            trend_map[str(d)] = {"date": str(d)}
            for s in all_sentiments:
                trend_map[str(d)][s] = 0
        trend_map[str(d)][sent] = count

    return {
        "total_calls_today": calls_today,
        "total_calls_yesterday": calls_yesterday,
        "total_calls_this_month": calls_this_month,
        "resolution_rate": round((resolved / total_all * 100) if total_all > 0 else 0, 1),
        "positive_percentage": round((positive / total_all * 100) if total_all > 0 else 0, 1),
        "negative_percentage": round((negative / total_all * 100) if total_all > 0 else 0, 1),
        "neutral_percentage": round((neutral / total_all * 100) if total_all > 0 else 0, 1),
        "category_distribution": dict(category_counts),
        "sentiment_distribution": {s: c for s, c in sorted(sentiment_counts, key=lambda x: -x[1])},
        "sentiment_trend": sorted(trend_map.values(), key=lambda x: x["date"]),
    }


def get_agent_performance(db: Session) -> list[dict]:
    agents = db.query(Agent).all()
    all_sentiments = [r[0] for r in db.query(Call.sentiment).distinct().all()]

    results = []
    for agent in agents:
        total = db.query(Call).filter(Call.agent_id == agent.id).count()
        if total == 0:
            continue

        sentiment_breakdown = {}
        for sent in all_sentiments:
            count = db.query(Call).filter(
                Call.agent_id == agent.id, Call.sentiment == sent
            ).count()
            sentiment_breakdown[sent] = count

        positive = sentiment_breakdown.get("Positive", 0)
        neutral = sentiment_breakdown.get("Neutral", 0)
        negative = total - positive - neutral
        resolved = db.query(Call).filter(
            Call.agent_id == agent.id, Call.resolved == True
        ).count()

        results.append({
            "agent_id": agent.id,
            "agent_name": agent.name,
            "team": agent.team,
            "total_calls": total,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "positive_percentage": round(positive / total * 100, 1),
            "negative_percentage": round(negative / total * 100, 1),
            "resolved_count": resolved,
            "resolution_rate": round(resolved / total * 100, 1),
        })

    results.sort(key=lambda x: x["positive_percentage"], reverse=True)
    return results


def get_category_trend(db: Session, days: int = 365) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(
            func.date(Call.timestamp).label("date"),
            Call.category,
            func.count(Call.id).label("count"),
        )
        .filter(Call.timestamp >= cutoff)
        .group_by(func.date(Call.timestamp), Call.category)
        .order_by(func.date(Call.timestamp))
        .all()
    )

    return [{"category": r.category, "date": str(r.date), "count": r.count} for r in rows]


def get_top_categories(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(Call.category, func.count(Call.id).label("count"))
        .group_by(Call.category)
        .order_by(desc("count"))
        .limit(limit)
        .all()
    )
    return [{"category": r.category, "count": r.count} for r in rows]


def update_daily_aggregate(db: Session, day: datetime) -> DailyAggregate:
    day_date = day.replace(hour=0, minute=0, second=0, microsecond=0)
    next_day = day_date + timedelta(days=1)

    total = db.query(Call).filter(Call.timestamp >= day_date, Call.timestamp < next_day).count()
    resolved = db.query(Call).filter(
        Call.timestamp >= day_date, Call.timestamp < next_day, Call.resolved == True
    ).count()
    positive = db.query(Call).filter(
        Call.timestamp >= day_date, Call.timestamp < next_day, Call.sentiment == "Positive"
    ).count()
    negative = db.query(Call).filter(
        Call.timestamp >= day_date, Call.timestamp < next_day, Call.sentiment == "Negative"
    ).count()
    neutral = db.query(Call).filter(
        Call.timestamp >= day_date, Call.timestamp < next_day, Call.sentiment == "Neutral"
    ).count()

    category_counts = (
        db.query(Call.category, func.count(Call.id))
        .filter(Call.timestamp >= day_date, Call.timestamp < next_day)
        .group_by(Call.category)
        .all()
    )
    top_category = max(category_counts, key=lambda x: x[1])[0] if category_counts else None

    existing = db.query(DailyAggregate).filter(DailyAggregate.date == day_date).first()
    if existing:
        existing.total_calls = total
        existing.resolved_count = resolved
        existing.positive_count = positive
        existing.negative_count = negative
        existing.neutral_count = neutral
        existing.top_category = top_category
    else:
        existing = DailyAggregate(
            date=day_date,
            total_calls=total,
            resolved_count=resolved,
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
            top_category=top_category,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def refresh_all_daily_aggregates(db: Session) -> int:
    dates = (
        db.query(func.date(Call.timestamp).label("day"))
        .distinct()
        .all()
    )
    count = 0
    for (day_str,) in dates:
        day = datetime.strptime(day_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        update_daily_aggregate(db, day)
        count += 1
    return count
