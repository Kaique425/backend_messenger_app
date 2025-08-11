import redis
from django.conf import settings

_client = None


def get_redis():
    global _client
    if _client is None:
        pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL_GATE,
            decode_responses=True,
            max_connections=128,
        )
        _client = redis.Redis(connection_pool=pool)
    return _client
