import logging

from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import get_settings
from app.core.security import hash_token

logger = logging.getLogger(__name__)


async def enforce_rate_limit(
    *, scope: str, identity: str, limit: int, window_seconds: int
) -> None:
    """Простой fixed-window лимит в Redis.

    Если Redis недоступен, вход не блокируем: для локальной разработки
    доступность важнее, а production-мониторинг должен поймать деградацию.
    """
    settings = get_settings()
    key = f"ratelimit:{scope}:{hash_token(identity.strip().lower())}"
    client = Redis.from_url(settings.redis_url, decode_responses=True)

    try:
        current = await client.incr(key)
        if current == 1:
            await client.expire(key, window_seconds)
        if current > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много попыток. Попробуйте позже.",
                headers={"Retry-After": str(window_seconds)},
            )
    except RedisError:
        logger.warning("Rate limit skipped: Redis is unavailable")
    finally:
        await client.aclose()
