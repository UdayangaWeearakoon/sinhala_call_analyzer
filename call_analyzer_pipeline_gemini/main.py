import logging
import os
import signal
import threading

import watcher
from worker import worker_loop

logger = logging.getLogger(__name__)

NUM_WORKERS = int(os.getenv("WORKERS", "1"))
shutdown_event = threading.Event()


def handle_sigterm(signum, frame):
    logger.info("SIGTERM received — shutting down...")
    shutdown_event.set()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        force=True,
    )
    for noisy in ("httpx", "httpcore", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    workers = []
    for i in range(NUM_WORKERS):
        t = threading.Thread(
            target=worker_loop,
            args=(f"worker-{i}", shutdown_event),
            daemon=True,
        )
        t.start()
        workers.append(t)

    wt = threading.Thread(target=watcher.main, daemon=True)
    wt.start()

    logger.info("Started %d workers + watcher", NUM_WORKERS)

    try:
        shutdown_event.wait()
    except KeyboardInterrupt:
        shutdown_event.set()

    for t in workers:
        t.join(timeout=30)

    logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
