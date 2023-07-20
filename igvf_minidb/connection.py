"""Caching GET response with Redis
"""
import json
import logging
import redis
import requests

from requests.adapters import (
    HTTPAdapter,
    Retry,
)
from igvf_minidb.redis_store import (
    set_redis_key_val,
    get_redis_val,
)


logger = logging.getLogger(__name__)


# global variables
username = None
password = None
endpoint = None
get_call_count = 0
get_call_cached_count = 0

# constants
CALLS_PER_LOG = 200


def set_endpoint(e):
    global endpoint
    if e.endswith("/"):
        raise ValueError("Trailing slash not allowed in endpoint.")
    endpoint = e


def set_username(u):
    global username
    username = u


def set_password(p):
    global password
    password = p


def get(url_query, write_cache=True):
    """
    Cached GET
    """
    global endpoint
    global username
    global password
    global get_call_count
    global get_call_cached_count

    if not endpoint:
        raise ValueError("Endpoint not defined.")

    url = f"{endpoint}/{url_query}"

    cached = get_redis_val(url)

    get_call_count = get_call_count + 1
    if cached:
        get_call_cached_count = get_call_cached_count + 1
    if get_call_count % CALLS_PER_LOG == 0:
        logger.info(
            f"numCalls. total:{get_call_count}, "
            f"cached:{get_call_cached_count}, "
            f"non-cached:{get_call_count-get_call_cached_count}"
        )

    if cached:
        return json.loads(cached)

    auth = (username, password) if username and password else None

    retries = Retry(
        total=3,
        backoff_factor=10,
        status_forcelist=[110, 408, 500, 502, 503, 504]
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retries)
    session.mount(endpoint, adapter)

    response = session.get(url, auth=auth)
    response.raise_for_status()

    raw_text = response.text

    if write_cache:
        set_redis_key_val(url, raw_text)

    return json.loads(response.text)
