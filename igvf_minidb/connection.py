"""Caching GET response with Redis
"""
import json
import logging
import redis
import requests

from igvf_minidb.redis_store import (
    set_redis_key_val,
    get_redis_val,
)


logger = logging.getLogger(__name__)


username = None
password = None
endpoint = None


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

    if not endpoint:
        raise ValueError("Endpoint not defined.")

    url = f"{endpoint}/{url_query}?format=json&frame=object"

    cached = get_redis_val(url)
    if cached:
        return json.loads(cached)

    auth = (username, password) if username and password else None
    response = requests.get(
        url,
        params={
            "method" : "GET", 
            "contentType": "application/json",
            "muteHttpExceptions": True,
        },
        auth=auth,
    )
    response.raise_for_status()

    raw_text = response.text

    if write_cache:
        set_redis_key_val(url, raw_text)

    return json.loads(response.text)
