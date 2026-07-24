import logging
import os
from typing import Optional

from flask import Blueprint, jsonify

import helpers
from helpers import ttl_cache

logger = logging.getLogger(__name__)

weather_bp = Blueprint("weather", __name__, url_prefix="/")

WEATHER_LOCATION: str = os.getenv("WEATHER_LOCATION", "48.2644222,11.5887688")
weather_api_url = f"https://wttr.in/{WEATHER_LOCATION}?format=j1"
headers = {}
TIMEOUT: Optional[int] = int(os.getenv("TIMEOUT", "60"))


@ttl_cache(seconds=300)
def fetch_weather() -> dict:
    return helpers.call_api(weather_api_url, headers, TIMEOUT, logger).json()


@weather_bp.route("/api/weather")
def get_weather():
    try:
        return jsonify(fetch_weather()), 200
    except helpers.ApiCallError as e:
        return jsonify({"error": str(e)}), e.status_code
