"""SHUNYA Loop Worker — standalone process for automated loop execution.

Usage:
    python3 worker.py              # Run in foreground (Ctrl+C to stop)
    nohup python3 worker.py &      # Run in background
    python3 worker.py --once       # Run a single cycle and exit

This is the production-ready loop runner. It loads the Flask app
and runs run_cycle() every 3 seconds with crash isolation.

For systemd/supervisor, run this as a managed service.
"""

import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("shunya-worker")


def run_worker(once: bool = False):
    """Run the SHUNYA execution loop as a standalone worker process."""
    os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", "postgresql://shunya:***@localhost:5432/shunya_db"))
    os.environ.setdefault("SECRET_KEY", "dev-secret-change-in-production")

    from app import create_app
    from app.runtime.loop import run_cycle

    app = create_app()
    cycle_count = 0

    logger.info("SHUNYA loop worker starting" + (" (single cycle)" if once else ""))
    print("[WORKER] SHUNYA loop worker started. Cycles every 3s. Ctrl+C to stop.")

    try:
        with app.app_context():
            while True:
                cycle_count += 1
                summary = run_cycle()
                actions = summary.get("actions_taken", 0)
                noops = summary.get("noops", 0)
                errors = summary.get("errors", [])

                if actions > 0 or errors:
                    logger.info(
                        "Cycle %d: %d actions, %d noops, %d errors",
                        cycle_count, actions, noops, len(errors),
                    )
                    if errors:
                        for err in errors[:3]:
                            logger.warning("  Error: %s", err)

                if once:
                    logger.info("Single cycle complete")
                    return

                time.sleep(3)
    except KeyboardInterrupt:
        logger.info("Worker stopped after %d cycles", cycle_count)
        print(f"[WORKER] Stopped after {cycle_count} cycles")


if __name__ == "__main__":
    once = "--once" in sys.argv
    run_worker(once=once)