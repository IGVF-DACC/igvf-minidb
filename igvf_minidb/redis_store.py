"""Key-value pair Caching based on Redis
"""
import logging
import redis


logger = logging.getLogger(__name__)


redis_host = "localhost"
redis_port = 6379


def set_redis_host(host):
    global redis_host
    redis_host = host


def set_redis_port(port):
    global redis_port
    redis_port = port


def set_redis_key_val(key, val):
    global redis_host
    global redis_port
    r = redis.Redis(host=redis_host, port=redis_port, db=0)
    return r.set(key, val)


def get_redis_val(key):
    global redis_host
    global redis_port
    r = redis.Redis(host=redis_host, port=redis_port, db=0)
    return r.get(key)
