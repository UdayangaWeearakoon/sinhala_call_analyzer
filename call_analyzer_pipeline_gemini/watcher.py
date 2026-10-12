import hashlib
import logging
import os
import shutil
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from sqlalchemy import text

from db import get_session

logger = logging.getLogger(__name__)

INCOMING = Path("incoming")
PROCESSING = Path("processing")
ARCHIVE = Path("archive")
ERROR_DIR = Path("error")


def compute_sha256(filepath, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            h = hashlib.sha256()
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        except PermissionError:
            if attempt == retries - 1:
                raise
            time.sleep(delay * (attempt + 1))


def process_file(filepath):
    if not os.path.exists(filepath):
        return

    filename = os.path.basename(filepath)
    content_hash = compute_sha256(filepath)

    session = get_session()
    try:
        existing = session.execute(
            text("SELECT id FROM transcripts WHERE content_hash = :hash"),
            {"hash": content_hash},
        ).fetchone()

        if existing:
            shutil.move(str(filepath), str(ARCHIVE / filename))
            logger.info("duplicate skipped: %s -> archive/", filename)
            return

        session.execute(
            text(
                "INSERT INTO transcripts (filename, content_hash, status) "
                "VALUES (:filename, :hash, 'pending')"
            ),
            {"filename": filename, "hash": content_hash},
        )
        shutil.move(str(filepath), str(PROCESSING / filename))
        session.commit()
        logger.info("new file: %s -> processing/", filename)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class WatcherHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        try:
            if os.path.exists(event.src_path):
                process_file(event.src_path)
        except Exception:
            logger.exception("Error processing %s", event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        try:
            if os.path.exists(event.src_path):
                process_file(event.src_path)
        except Exception:
            logger.exception("Error processing %s", event.src_path)


def main():
    for d in (INCOMING, PROCESSING, ARCHIVE, ERROR_DIR):
        d.mkdir(exist_ok=True)

    observer = Observer()
    handler = WatcherHandler()
    observer.schedule(handler, str(INCOMING), recursive=False)
    observer.start()
    logger.info("Watching %s ...", INCOMING.resolve())

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
