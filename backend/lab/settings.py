import os
from pathlib import Path

from sqlalchemy import URL

DB_URL = os.getenv("DATABASE_URL") or URL.create(
    "mysql+pymysql",
    username=os.getenv("MYSQL_USER", "light_lab"),
    password=os.getenv("MYSQL_PASSWORD", "local-light-lab"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    database=os.getenv("MYSQL_DATABASE", "light_cal"),
    query={"charset": "utf8mb4"},
)
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
JWT_SECRET = os.getenv("JWT_SECRET", "local-greenhouse-light-cal-signing-secret")
SEED_DEMO = os.getenv("SEED_DEMO", "false").lower() == "true"
ARTIFACT_PATH = Path(os.getenv("ARTIFACT_PATH", "/srv/light"))
SEED_PASSWORD = "SeedLight2026!"
BLOCK_MINUTES = 10
CHANNEL = "light:calibration:ready"
