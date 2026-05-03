import os
import sys
import json
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, SessionLocal
from src.database.models import Call, Agent
from src.inference import CallAnalyticsPredictor

AGENT_NAMES = [
    ("Kamal Perera", "Team A"),
    ("Nimali Silva", "Team A"),
    ("Ruwan Fernando", "Team B"),
    ("Dilrukshi Jayawardena", "Team B"),
    ("Tharindu Bandara", "Team C"),
]


def seed_database():
    init_db()
    db = SessionLocal()

    print("Loading training data...")
    with open("data/processed/combined.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Found {len(data)} transcripts to seed.")

    print("Loading ML predictor...")
    predictor = CallAnalyticsPredictor()

    print("Creating agents...")
    agents = []
    for name, team in AGENT_NAMES:
        agent = db.query(Agent).filter(Agent.name == name).first()
        if not agent:
            agent = Agent(name=name, team=team, joined_date=datetime.now(timezone.utc) - timedelta(days=365))
            db.add(agent)
            db.commit()
            db.refresh(agent)
        agents.append(agent)

    existing_count = db.query(Call).count()
    if existing_count > 0:
        print(f"Skipping: {existing_count} calls already exist in DB.")
        db.close()
        return

    print("Running inference on all transcripts and seeding calls...")
    call_date_start = datetime.now(timezone.utc) - timedelta(days=180)
    call_date_end = datetime.now(timezone.utc)

    for i, item in enumerate(data):
        transcript = item["transcript"]

        result = predictor.predict(transcript)

        random_seconds = random.randint(60, 1800)
        random_date = call_date_start + timedelta(
            seconds=random.randint(0, int((call_date_end - call_date_start).total_seconds()))
        )

        agent = random.choice(agents)
        resolved = random.choices([True, False], weights=[65, 35])[0]

        call = Call(
            transcript=transcript,
            category=result["category"],
            sentiment=result["sentiment"],
            category_confidence=result["category_confidence"],
            sentiment_confidence=result["sentiment_confidence"],
            timestamp=random_date,
            call_duration=random_seconds,
            agent_id=agent.id,
            customer_phone=f"07{random.randint(0,9)}{random.randint(1000000, 9999999)}",
            resolved=resolved,
        )
        db.add(call)

        if (i + 1) % 10 == 0:
            db.commit()
            print(f"  Seeded {i + 1}/{len(data)} calls...")

    db.commit()
    print(f"\nSeed complete! {len(data)} calls added to database.")

    total = db.query(Call).count()
    print(f"Total calls in DB: {total}")

    pos = db.query(Call).filter(Call.sentiment == "Positive").count()
    neg = db.query(Call).filter(Call.sentiment == "Frustrated").count()
    neu = db.query(Call).filter(Call.sentiment == "Neutral").count()
    print(f"  Positive: {pos}")
    print(f"  Negative: {neg}")
    print(f"  Neutral: {neu}")

    db.close()


if __name__ == "__main__":
    seed_database()
