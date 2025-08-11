from django.conf import settings

from .redis_client import get_redis

_LUA = """
local cur = redis.call('GET', KEYS[1])
local cur_rank = cur and tonumber(cur) or -1
local new_rank = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])
if new_rank <= cur_rank then return 0 end
redis.call('SET', KEYS[1], new_rank, 'EX', ttl)
return 1
"""

_script = None


def _script_obj():
    global _script
    if _script is None:
        _script = get_redis().register_script(_LUA)
    return _script


def should_enqueue_status(wamid: str, new_status: str, ttl: int | None = None) -> bool:
    rank = settings.MESSAGE_STATUS_RANK.get(new_status)
    if rank is None:
        print(f"[WARNING] - Not mapped status {new_status}")
        return False
    key = f"msgstat:{wamid}"
    ttl = ttl or settings.TTL_STATUS_SECONDS

    ret = _script_obj()(
        keys=[key],
        args=[rank, ttl],
    )
    return ret == 1
