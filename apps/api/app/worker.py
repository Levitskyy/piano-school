from arq import cron
from arq.connections import RedisSettings

from app.config import get_settings
from app.db import SessionLocal
from app.services.payments import release_expired_orders


async def ping(ctx: dict) -> str:
    return "pong"


async def release_expired_orders_job(ctx: dict) -> None:
    async with SessionLocal() as session:
        await release_expired_orders(session)


class WorkerSettings:
    functions = [ping]
    cron_jobs = [cron(release_expired_orders_job, minute=set(range(0, 60, 5)))]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
