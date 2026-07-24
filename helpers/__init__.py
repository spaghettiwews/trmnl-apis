import json
import threading
import time
from datetime import datetime, timezone
from functools import wraps

import requests
from dateutil.relativedelta import relativedelta


class ApiCallError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


def ttl_cache(seconds: int):
    """Thread-safe in-memory TTL cache. Each decorated function has its own store."""
    def decorator(fn):
        _cache: dict = {}
        _lock = threading.Lock()

        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = time.monotonic()
            key = (args, tuple(sorted(kwargs.items())))
            with _lock:
                entry = _cache.get(key)
                if entry is not None:
                    result, expires_at = entry
                    if now < expires_at:
                        return result
            result = fn(*args, **kwargs)
            with _lock:
                _cache[key] = (result, now + seconds)
            return result

        return wrapper
    return decorator


def call_api(url, headers, timeout, logger):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)

        # Check for HTTP errors (4xx or 5xx)
        response.raise_for_status()

        logger.info("Successfully received response from the API.")
        return response

    except requests.exceptions.Timeout:
        logger.error(f"API request timed out after {timeout} seconds.")
        raise ApiCallError("API request timed out.", 504)
    except requests.exceptions.HTTPError as e:
        # Specific logging for bad status codes (400, 404, 500, etc.)
        logger.error(
            f"HTTP Error retrieving response (Status: {e.response.status_code}): {e}"
        )
        raise ApiCallError(
            f"API returned an error: {e.response.reason}", e.response.status_code
        )
    except requests.exceptions.ConnectionError as e:
        # Catches general connection/DNS errors
        logger.critical(
            f"Connection error encountered: {e}. Check network connectivity."
        )
        raise ApiCallError(
            "Could not connect to the API. Please check connectivity.", 503
        )
    except requests.exceptions.RequestException as e:
        # Catches any other requests related error
        logger.exception(f"An unexpected request error occurred: {e}")
        raise ApiCallError("An unexpected network error occurred.", 503)
    except json.JSONDecodeError:
        # Catches cases where the response is not valid JSON
        logger.error("Received response was not valid JSON.")
        raise ApiCallError("The API returned invalid data format.", 500)
    except ApiCallError:
        raise
    except Exception as e:
        # Catches any other unexpected Python error
        logger.exception(f"An unexpected server error occurred during fetching: {e}")
        raise ApiCallError("An internal server error occurred.", 500)


def format_date(timestamp: str, format: str = "relative", now: datetime = None) -> str:
    """
    Return either a formatted date or relative time in weeks only.

    :param timestamp: ISO 8601 string
    :param format: "date" or "relative"
    :param now: optional override for current time (timezone-aware)
    """
    ts = datetime.fromisoformat(timestamp)

    if now is None:
        now = datetime.now(timezone.utc)

    if format == "date":
        return ts.strftime("%A, %d %B")

    elif format == "relative":
        delta = now - ts
        weeks = delta.days // 7

        if weeks <= 0:
            return "less than a week ago"

        return f"{weeks} week{'s' if weeks != 1 else ''} ago"

    else:
        raise ValueError("format must be either 'date' or 'relative'")


def iso_to_time(iso_string: str) -> str:
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime("%H:%M")


def calc_time_diff(start: datetime, end: datetime) -> str:
    """
    Returns the difference between two datetimes as:
    'X months, X days, X hours, X minutes'

    Handles comparisons between offset-naive and offset-aware datetimes
    by converting naive datetimes to UTC-aware.
    """

    def make_aware(dt: datetime) -> datetime:
        # If datetime is naive, assume UTC
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    start = make_aware(start)
    end = make_aware(end)

    # Ensure start is before end
    if start > end:
        start, end = end, start

    diff = relativedelta(end, start)

    parts = []

    if diff.years:
        parts.append(f"{diff.years} year{'s' if diff.years != 1 else ''}")

    if diff.months:
        parts.append(f"{diff.months} month{'s' if diff.months != 1 else ''}")

    if diff.days:
        parts.append(f"{diff.days} day{'s' if diff.days != 1 else ''}")

    if diff.hours:
        parts.append(f"{diff.hours} hour{'s' if diff.hours != 1 else ''}")

    if diff.minutes:
        parts.append(f"{diff.minutes} minute{'s' if diff.minutes != 1 else ''}")

    return ", ".join(parts) if parts else "0 minutes"
