import argparse
import asyncio
import logging
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline")


def resolve_dir(value: str | None, env_var: str, default: Path) -> Path:
    if value:
        return Path(value)
    env = os.getenv(env_var)
    if env:
        return Path(env)
    return default


async def run_once(predictor, incoming_dir, processed_dir, error_dir) -> dict:
    from src.pipeline.processor import process_all_files

    stats = await process_all_files(incoming_dir, processed_dir, error_dir, predictor)
    return stats


async def run_watch(predictor, incoming_dir, processed_dir, error_dir, interval: int):
    from src.database import init_db, close_db

    await init_db()
    logger.info("Watch mode enabled (polling every %ds)", interval)
    try:
        while True:
            try:
                stats = await run_once(predictor, incoming_dir, processed_dir, error_dir)
                if stats["total"] > 0:
                    logger.info("Poll cycle complete: %s", stats)
            except Exception as e:
                logger.error("Poll cycle failed: %s", e)
            await asyncio.sleep(interval)
    finally:
        await close_db()


def main():
    parser = argparse.ArgumentParser(
        description="Sinhala Call Analytics - Folder Transcript Pipeline",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch mode: poll for new files continuously",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Poll interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--incoming",
        help="Incoming dir (overrides PIPELINE_INCOMING_DIR env / default)",
    )
    parser.add_argument(
        "--processed",
        help="Processed dir (overrides PIPELINE_PROCESSED_DIR env / default)",
    )
    parser.add_argument(
        "--error",
        help="Error dir (overrides PIPELINE_ERROR_DIR env / default)",
    )
    parser.add_argument(
        "--models-dir",
        default="data/models",
        help="ML models directory (default: data/models)",
    )
    args = parser.parse_args()

    root = Path("data") / "transcripts"

    incoming_dir = resolve_dir(args.incoming, "PIPELINE_INCOMING_DIR", root / "incoming")
    processed_dir = resolve_dir(args.processed, "PIPELINE_PROCESSED_DIR", root / "processed")
    error_dir = resolve_dir(args.error, "PIPELINE_ERROR_DIR", root / "error")

    logger.info("Directories:")
    logger.info("  Incoming:  %s", incoming_dir.resolve())
    logger.info("  Processed: %s", processed_dir.resolve())
    logger.info("  Error:     %s", error_dir.resolve())

    from src.inference import CallAnalyticsPredictor

    predictor = CallAnalyticsPredictor(models_dir=args.models_dir)

    if args.watch:
        asyncio.run(run_watch(predictor, incoming_dir, processed_dir, error_dir, args.interval))
    else:
        async def _oneshot():
            from src.database import init_db, close_db

            await init_db()
            try:
                return await run_once(predictor, incoming_dir, processed_dir, error_dir)
            finally:
                await close_db()

        asyncio.run(_oneshot())


if __name__ == "__main__":
    main()
