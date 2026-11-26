import logging
from pathlib import Path
import time

from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text

from .calibration_service import try_fit
from .database import open_session
from .settings import CHANNEL, REDIS_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("light.worker")
beat = Path("/tmp/light-worker-heartbeat")


def main():
    queue = Redis.from_url(REDIS_URL, socket_timeout=4, socket_connect_timeout=3)
    while True:
        try:
            with open_session() as db:
                db.execute(text("SELECT 1"))
                processed = try_fit(db)
            queue.ping()
            beat.touch()
            if not processed:
                queue.brpop(CHANNEL, timeout=3)
        except (RedisError, OSError):
            logger.exception("Worker dependency unavailable")
            time.sleep(3)
        except Exception:
            logger.exception("Fit failed unexpectedly; queued record retained for retry")
            time.sleep(5)


if __name__ == "__main__":
    main()
