import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("pipeline.processor")


async def process_file(filepath: Path, predictor, processed_dir: Path, error_dir: Path) -> dict:
    filename = filepath.name

    try:
        transcript = filepath.read_text(encoding="utf-8").strip()
        if not transcript:
            raise ValueError("Empty transcript")

        from src.utils.hash_utils import generate_sha256_hash
        from src.database.repository import get_call_by_hash

        file_hash = generate_sha256_hash(transcript)
        existing = await get_call_by_hash(file_hash)
        if existing:
            filepath.unlink(missing_ok=True)
            logger.info("Deleted duplicate: %s (already exists as call #%s)", filename, existing.id)
            return {"file": filename, "status": "skipped", "detail": f"Duplicate (call #{existing.id})"}

        result = predictor.predict(transcript)

        from src.database.repository import create_call, update_daily_aggregate

        call_data = {
            "transcript": transcript,
            "category": result["category"],
            "sentiment": result["sentiment"],
            "category_confidence": result["category_confidence"],
            "sentiment_confidence": result["sentiment_confidence"],
            "filename": filename,
            "file_hash": file_hash,
            "source_type": "folder_pipeline",
            "uploaded_at": datetime.now(timezone.utc),
        }
        db_call = await create_call(call_data)
        await update_daily_aggregate(db_call.timestamp)

        _move_file(filepath, processed_dir)

        logger.info(
            "Processed: %s → call #%s (%s, %s)",
            filename, db_call.id, result["category"], result["sentiment"],
        )
        return {"file": filename, "status": "processed", "detail": f"Call #{db_call.id}"}

    except Exception as e:
        logger.error("Failed to process %s: %s", filename, e)
        _move_file(filepath, error_dir)
        return {"file": filename, "status": "failed", "detail": str(e)}


def _move_file(src: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    dest = dst_dir / src.name
    if dest.exists():
        stem = src.stem
        suffix = src.suffix
        dest = dst_dir / f"{stem}_{int(datetime.now().timestamp())}{suffix}"
    src.rename(dest)


async def process_all_files(
    incoming_dir: Path,
    processed_dir: Path,
    error_dir: Path,
    predictor,
    min_file_age_secs: int = 30,
) -> dict:
    incoming_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    error_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now().timestamp()
    files = sorted(
        [f for f in incoming_dir.iterdir() if f.suffix.lower() == ".txt"],
        key=lambda p: p.stat().st_mtime,
    )
    files = [f for f in files if now - f.stat().st_mtime >= min_file_age_secs]

    if not files:
        return {"total": 0, "processed": 0, "skipped": 0, "failed": 0}

    logger.info("Found %d file(s) to process in %s", len(files), incoming_dir)

    stats = {"total": len(files), "processed": 0, "skipped": 0, "failed": 0}

    for filepath in files:
        result = await process_file(filepath, predictor, processed_dir, error_dir)
        stats[result["status"]] = stats.get(result["status"], 0) + 1

    logger.info("Batch complete: %s", stats)
    return stats
