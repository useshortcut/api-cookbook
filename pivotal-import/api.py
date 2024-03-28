"""Helper functions for communicating with the Shortcut API.

Expects the Shortcut token to be set in the SHORTCUT_API_TOKEN
environment variable.

"""

import os
import logging

import requests

# FIXME Make INFO default upon public release
logging.basicConfig(level=logging.DEBUG)  # Change to INFO or DEBUG as needed

# Logging
logger = logging.getLogger(__name__)

# API Helpers
sc_token = os.getenv("SHORTCUT_API_TOKEN")
api_url_base = "https://api.app.shortcut.com/api/v3"
headers = {
    "Shortcut-Token": sc_token,
    "Accept": "application/json; charset=utf-8",
    "Content-Type": "application/json",
}


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
    resp.raise_for_status()
    return resp.json()


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
