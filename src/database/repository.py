from datetime import datetime, timedelta, timezone, date
from typing import Optional
from sqlalchemy import select, func, case, and_, Text
import src.database as db
from src.database.models import Call, DailyAggregate


NEGATIVE_SENTIMENTS = ["Negative"]


async def create_call(call_data: dict) -> Call:
    async with db.get_session() as session:
        call = Call(**call_data)
        session.add(call)
        await session.flush()
        await session.commit()
        return call


async def get_calls(
    skip: int = 0,
    limit: int = 50,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
) -> tuple[list[Call], int]:
    async with db.get_session() as session:
        filters = []
        if date_from or date_to:
            ts_filter = []
            if date_from:
                ts_filter.append(Call.timestamp >= date_from)
            if date_to:
                ts_filter.append(Call.timestamp <= date_to)
            filters.append(and_(*ts_filter))
        if category:
            filters.append(Call.category == category)
        if sentiment:
            filters.append(Call.sentiment == sentiment)

        count_query = select(func.count(Call.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        query = select(Call)
        if filters:
            query = query.where(and_(*filters))
        query = query.order_by(Call.timestamp.desc()).offset(skip).limit(limit)
        result = await session.execute(query)
        calls = list(result.scalars().all())
        return calls, total


async def get_call_by_id(call_id: int) -> Optional[Call]:
    async with db.get_session() as session:
        result = await session.execute(select(Call).where(Call.id == call_id))
        return result.scalar_one_or_none()


async def get_call_by_hash(file_hash: str) -> Optional[Call]:
    async with db.get_session() as session:
        result = await session.execute(
            select(Call).where(Call.file_hash == file_hash)
        )
        return result.scalar_one_or_none()


async def get_overview_stats() -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    month_start = today_start.replace(day=1)
    thirty_days_ago = today_start - timedelta(days=30)

    async with db.get_session() as session:
        tr_result = await session.execute(
            select(
                func.count(Call.id).label("total_all"),
                func.sum(case((Call.resolved == True, 1), else_=0)).label("resolved"),
                func.sum(case((Call.timestamp >= today_start, 1), else_=0)).label("calls_today"),
                func.sum(
                    case(
                        (and_(Call.timestamp >= yesterday_start, Call.timestamp < today_start), 1),
                        else_=0,
                    )
                ).label("calls_yesterday"),
                func.sum(case((Call.timestamp >= month_start, 1), else_=0)).label("calls_this_month"),
            )
        )
        row = tr_result.one()
        total_all = row.total_all or 0
        resolved = row.resolved or 0
        calls_today = row.calls_today or 0
        calls_yesterday = row.calls_yesterday or 0
        calls_this_month = row.calls_this_month or 0

        sent_result = await session.execute(
            select(Call.sentiment, func.count(Call.id).label("count"))
            .group_by(Call.sentiment)
        )
        sentiment_map = {r.sentiment: r.count for r in sent_result.all()}

        positive = sentiment_map.get("Positive", 0)
        neutral = sentiment_map.get("Neutral", 0)
        negative = sum(sentiment_map.get(s, 0) for s in NEGATIVE_SENTIMENTS)

        cat_result = await session.execute(
            select(Call.category, func.count(Call.id).label("count"))
            .group_by(Call.category)
        )
        category_dist = {r.category: r.count for r in cat_result.all()}

        trend_result = await session.execute(
            select(
                func.date(Call.timestamp).label("day"),
                Call.sentiment,
                func.count(Call.id).label("count"),
            )
            .where(Call.timestamp >= thirty_days_ago)
            .group_by(func.date(Call.timestamp), Call.sentiment)
            .order_by(func.date(Call.timestamp))
        )
        trend_rows = trend_result.all()

        all_sentiments = {r.sentiment for r in trend_rows}
        trend_map = {}
        for r in trend_rows:
            d = str(r.day)
            sent = r.sentiment
            count = r.count
            if d not in trend_map:
                trend_map[d] = {"date": d}
                for s in all_sentiments:
                    trend_map[d][s] = 0
            trend_map[d][sent] = count

        return {
            "total_calls_today": calls_today,
            "total_calls_yesterday": calls_yesterday,
            "total_calls_this_month": calls_this_month,
            "resolution_rate": round((resolved / total_all * 100) if total_all > 0 else 0, 1),
            "positive_percentage": round((positive / total_all * 100) if total_all > 0 else 0, 1),
            "negative_percentage": round((negative / total_all * 100) if total_all > 0 else 0, 1),
            "neutral_percentage": round((neutral / total_all * 100) if total_all > 0 else 0, 1),
            "category_distribution": dict(sorted(category_dist.items(), key=lambda x: -x[1])),
            "sentiment_distribution": dict(sorted(sentiment_map.items(), key=lambda x: -x[1])),
            "sentiment_trend": sorted(trend_map.values(), key=lambda x: x["date"]),
        }


async def get_category_trend(days: int = 365) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    async with db.get_session() as session:
        result = await session.execute(
            select(
                func.date(Call.timestamp).label("day"),
                Call.category,
                func.count(Call.id).label("count"),
            )
            .where(Call.timestamp >= cutoff)
            .group_by(func.date(Call.timestamp), Call.category)
            .order_by(func.date(Call.timestamp))
        )
        return [
            {"category": r.category, "date": str(r.day), "count": r.count}
            for r in result.all()
        ]


async def get_top_categories(limit: int = 10) -> list[dict]:
    async with db.get_session() as session:
        result = await session.execute(
            select(Call.category, func.count(Call.id).label("count"))
            .group_by(Call.category)
            .order_by(func.count(Call.id).desc())
            .limit(limit)
        )
        return [{"category": r.category, "count": r.count} for r in result.all()]


async def update_daily_aggregate(day: datetime) -> DailyAggregate:
    day_date = day.replace(hour=0, minute=0, second=0, microsecond=0)
    next_day = day_date + timedelta(days=1)

    async with db.get_session() as session:
        stats_result = await session.execute(
            select(
                func.count(Call.id).label("total_calls"),
                func.sum(case((Call.resolved == True, 1), else_=0)).label("resolved_count"),
                func.sum(case((Call.sentiment == "Positive", 1), else_=0)).label("positive_count"),
                func.sum(
                    case(*[(Call.sentiment == s, 1) for s in NEGATIVE_SENTIMENTS], else_=0)
                ).label("negative_count"),
                func.sum(case((Call.sentiment == "Neutral", 1), else_=0)).label("neutral_count"),
            )
            .where(and_(Call.timestamp >= day_date, Call.timestamp < next_day))
        )
        s = stats_result.one()

        top_result = await session.execute(
            select(Call.category, func.count(Call.id).label("count"))
            .where(and_(Call.timestamp >= day_date, Call.timestamp < next_day))
            .group_by(Call.category)
            .order_by(func.count(Call.id).desc())
            .limit(1)
        )
        top_row = top_result.one_or_none()
        top_category = top_row.category if top_row else None

        existing = await session.execute(
            select(DailyAggregate).where(DailyAggregate.date == day_date)
        )
        agg = existing.scalar_one_or_none()

        if agg:
            agg.total_calls = s.total_calls or 0
            agg.resolved_count = s.resolved_count or 0
            agg.positive_count = s.positive_count or 0
            agg.negative_count = s.negative_count or 0
            agg.neutral_count = s.neutral_count or 0
            agg.top_category = top_category
        else:
            agg = DailyAggregate(
                date=day_date,
                total_calls=s.total_calls or 0,
                resolved_count=s.resolved_count or 0,
                positive_count=s.positive_count or 0,
                negative_count=s.negative_count or 0,
                neutral_count=s.neutral_count or 0,
                top_category=top_category,
            )
            session.add(agg)

        await session.flush()
        await session.commit()
        return agg


async def refresh_all_daily_aggregates() -> int:
    async with db.get_session() as session:
        result = await session.execute(
            select(func.date(Call.timestamp).label("day")).distinct()
        )
        rows = result.all()
        count = 0
        for r in rows:
            day = datetime.combine(r.day, datetime.min.time()).replace(tzinfo=timezone.utc)
            await update_daily_aggregate(day)
            count += 1
        return count
