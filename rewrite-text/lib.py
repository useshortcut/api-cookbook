"""Helper functions for communicating with the Shortcut API.

Expects the Shortcut token to be set in the SHORTCUT_API_TOKEN
environment variable.

"""

from datetime import datetime
import sys
import os
import logging

from pyrate_limiter import Duration, InMemoryBucket, Limiter, Rate  # type: ignore
import requests

# Logging
logger = logging.getLogger(__name__)

# Rate limiting. See https://developer.shortcut.com/api/rest/v3#Rate-Limiting
# The Shortcut API limit is 200 per minute; the 200th request within 60 seconds
# will receive an HTTP 429 response.
#
# The rate limiting config below sets an in-memory limit that is just below
# Shortcut's rate limit to reduce the possibility of being throttled, and sets
# the amount of time it will wait once it reaches that limit to just
# over a minute to account for possible computer clock differences.
max_requests_per_minute = 200
rate = Rate(max_requests_per_minute - 5, Duration.MINUTE)
bucket = InMemoryBucket([rate])
max_limiter_delay_seconds = 70
limiter = Limiter(
    bucket, raise_when_fail=True, max_delay=Duration.SECOND * max_limiter_delay_seconds
)


def rate_mapping(*args, **kwargs):
    return "shortcut-api-request", 1


rate_decorator = limiter.as_decorator()


def print_rate_limiting_explanation():
    printerr(
        f"""[Note] This script adheres to the Shortcut API rate limit of {max_requests_per_minute} requests per minute.
       It may pause for up to {max_limiter_delay_seconds} seconds during processing to avoid request throttling."""
    )


# API Helpers
sc_token = os.getenv("SHORTCUT_API_TOKEN")
api_url_base = "https://api.app.shortcut.com/api/v3"
headers = {
    "Shortcut-Token": sc_token,
    "Accept": "application/json; charset=utf-8",
    "Content-Type": "application/json",
    "User-Agent": "shortcut-api-cookbook/0.0.1-alpha1",
}


@rate_decorator(rate_mapping)
def sc_get(path, params={}):
    """
    Make a GET api call.

    Serializes params as url query parameters.
    """
    url = api_url_base + path
    logger.debug("GET url=%s params=%s headers=%s" % (url, params, headers))
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


@rate_decorator(rate_mapping)
def sc_post(path, data={}):
    """Make a POST api call.

    Typically used to create an entity. Other types of requests that
    are either expensive or need consistent parameter serialization
    may also use a POST request.  Serializes params as JSON in the
    request body.

    """
    url = api_url_base + path
    logger.debug("POST url=%s params=%s headers=%s" % (url, data, headers))
    resp = requests.post(url, headers=headers, json=data)
    logger.debug(f"POST response: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    return resp.json()


@rate_decorator(rate_mapping)
def sc_put(path, data={}):
    """
    Make a PUT api call.

    Typically used to update an entity.
    Serializes params as JSON in the request body.
    """
    url = api_url_base + path
    logger.debug("PUT url=%s params=%s headers=%s" % (url, data, headers))
    resp = requests.put(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()


def printerr(s):
    print(s, file=sys.stderr)


def validate_environment():
    """
    Validate environment settings that must be in place to populate and load
    the default configuration for this script.
    """
    problems = []
    if sc_token is None:
        problems.append(
            " - You must define a SHORTCUT_API_TOKEN environment variable with your Shortcut API token."
        )
    if problems:
        msg = "\n".join(problems)
        printerr(f"Problems:\n{msg}")
        sys.exit(1)


def now_ts():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
