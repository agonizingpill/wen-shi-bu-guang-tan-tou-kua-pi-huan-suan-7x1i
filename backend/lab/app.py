from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from . import auth, calibration_routes, installation, readings, segment_routes
from .database import initialize
from .middlewares import correlate, prevent_stale_session, reject_integrity_conflict
from .settings import REDIS_URL, SEED_DEMO


@asynccontextmanager
async def startup(_app):
    initialize()
    if SEED_DEMO:
        from scripts.seed_demo import seed
        try:
            seed()
        except Exception:
            logging.getLogger(__name__).exception("Demo seed failed")
    yield


app = FastAPI(title="鹿栖育苗 · 补光基准工作台", lifespan=startup)
app.middleware("http")(prevent_stale_session)
app.middleware("http")(correlate)
app.add_exception_handler(IntegrityError, reject_integrity_conflict)

for module in (auth, installation, readings, segment_routes, calibration_routes):
    app.include_router(module.router)


@app.get("/health")
def health(db: auth.Db):
    try:
        db.execute(text("SELECT 1"))
        Redis.from_url(REDIS_URL, socket_connect_timeout=1, socket_timeout=1).ping()
    except (RedisError, SQLAlchemyError) as error:
        raise HTTPException(503, "数据或计算队列尚未就绪。") from error
    return {"status": "ok", "database": "mysql", "queue": "redis"}
