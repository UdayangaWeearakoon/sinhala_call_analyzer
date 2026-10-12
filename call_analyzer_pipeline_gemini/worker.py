import logging
import os
import shutil
import threading
import time
from pathlib import Path

from sqlalchemy import text
from tenacity import RetryError

from db import get_session
from classifier import (
    classify,
    classify_transcript_batch,
    ClassificationSchemaError,
    is_retryable,
)

logger = logging.getLogger(__name__)

PROCESSING = Path("processing")
ARCHIVE = Path("archive")
ERROR_DIR = Path("error")

POLL_INTERVAL = 2
MAX_RETRIES = 5
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5"))
BATCH_WAIT_SECONDS = int(os.getenv("BATCH_WAIT_SECONDS", "60"))


def claim_batch(session, worker_id, limit):
    rows = session.execute(
        text("""
            SELECT id, filename FROM transcripts
            WHERE status = 'pending'
            LIMIT :limit
            FOR UPDATE
        """),
        {"limit": limit},
    ).fetchall()

    if not rows:
        return []

    result = []
    for row in rows:
        session.execute(
            text("""
                UPDATE transcripts
                SET status = 'processing', claimed_by = :worker, claimed_at = NOW()
                WHERE id = :id
            """),
            {"worker": worker_id, "id": row[0]},
        )
        result.append({"id": row[0], "filename": row[1]})
    return result


def _process_batch(session, claimed_rows):
    items = []
    valid_rows = []

    for row in claimed_rows:
        filepath = PROCESSING / row["filename"]
        try:
            if not filepath.exists():
                raise FileNotFoundError(f"File not found: {filepath}")
            content = filepath.read_text(encoding="utf-8")
            if not content.strip():
                raise ValueError(f"Empty file: {filepath}")
            items.append({"id": str(row["id"]), "text": content})
            valid_rows.append(row)
        except (FileNotFoundError, ValueError) as e:
            _fatal(session, row, filepath, str(e))

    if not items:
        return

    try:
        results = classify_transcript_batch(items)
    except ClassificationSchemaError as e:
        for row in valid_rows:
            _fatal(session, row, PROCESSING / row["filename"], str(e))
        return
    except RetryError as e:
        cause = str(e.last_attempt.exception())
        for row in valid_rows:
            _retryable_fail(session, row, PROCESSING / row["filename"], cause)
        return
    except Exception as e:
        if is_retryable(e):
            for row in valid_rows:
                _retryable_fail(session, row, PROCESSING / row["filename"], str(e))
        else:
            for row in valid_rows:
                _fatal(session, row, PROCESSING / row["filename"], str(e))
        return

    result_by_id = {r.id: r for r in results}
    for row in valid_rows:
        filepath = PROCESSING / row["filename"]
        result = result_by_id.get(str(row["id"]))
        if result:
            with session.begin():
                session.execute(
                    text("""
                        UPDATE transcripts
                        SET status = 'completed', category = :cat, confidence = :conf
                        WHERE id = :id
                    """),
                    {"id": row["id"], "cat": result.category, "conf": result.confidence},
                )
            shutil.move(str(filepath), str(ARCHIVE / row["filename"]))
            logger.info("completed %s -> archive/ [%s]", row["filename"], result.category)
        else:
            logger.warning("No result returned for %s in batch response — will retry", row["filename"])
            _retryable_fail(session, row, filepath, "No result returned in batch response")


def worker_loop(worker_id, shutdown_event=None):
    if shutdown_event is None:
        shutdown_event = threading.Event()

    logger.info("Worker %s started", worker_id)

    while not shutdown_event.is_set():
        session = get_session()
        try:
            batch = []
            deadline = None

            while len(batch) < BATCH_SIZE and not shutdown_event.is_set():
                limit = BATCH_SIZE - len(batch)
                with session.begin():
                    newly = claim_batch(session, worker_id, limit)

                if newly:
                    batch.extend(newly)
                    if deadline is None:
                        deadline = time.time() + BATCH_WAIT_SECONDS
                else:
                    time.sleep(POLL_INTERVAL)
                    if not batch:
                        continue

                if len(batch) >= BATCH_SIZE:
                    break
                if deadline and time.time() >= deadline:
                    break

                time.sleep(POLL_INTERVAL)

            if not batch:
                continue

            _process_batch(session, batch)

        except Exception:
            logger.exception("Worker %s unhandled error", worker_id)
        finally:
            session.close()


def _fatal(session, claimed, filepath, err_msg):
    with session.begin():
        session.execute(
            text("""
                UPDATE transcripts
                SET status = 'dead_letter', last_error = :err
                WHERE id = :id
            """),
            {"id": claimed["id"], "err": err_msg},
        )
    if filepath.exists():
        shutil.move(str(filepath), str(ERROR_DIR / claimed["filename"]))
    logger.error("dead_letter %s: %s", claimed["filename"], err_msg)


def _retryable_fail(session, claimed, filepath, err_msg):
    with session.begin():
        session.execute(
            text("""
                UPDATE transcripts
                SET retry_count = retry_count + 1, last_error = :err
                WHERE id = :id
            """),
            {"id": claimed["id"], "err": err_msg},
        )

        row = session.execute(
            text("SELECT retry_count FROM transcripts WHERE id = :id"),
            {"id": claimed["id"]},
        ).fetchone()
        current_retries = row[0] if row else 0

        if current_retries >= MAX_RETRIES:
            session.execute(
                text("UPDATE transcripts SET status = 'dead_letter' WHERE id = :id"),
                {"id": claimed["id"]},
            )
            if filepath.exists():
                shutil.move(str(filepath), str(ERROR_DIR / claimed["filename"]))
            logger.warning("dead_letter %s after %d retries", claimed["filename"], MAX_RETRIES)
        else:
            session.execute(
                text("UPDATE transcripts SET status = 'pending' WHERE id = :id"),
                {"id": claimed["id"]},
            )
            logger.info("retry later %s (retry_count=%d)", claimed["filename"], current_retries)
