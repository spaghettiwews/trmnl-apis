import logging
import os
from typing import Optional

from dotenv import load_dotenv
from flask import Blueprint, jsonify

import helpers

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

weather_bp = Blueprint("weather", __name__, url_prefix="/")

weather_api_url = "https://wttr.in/48.2644222,11.5887688?format=j1"
headers = {}
TIMEOUT: Optional[int] = int(os.getenv("TIMEOUT", "60"))


@weather_bp.route("/api/weather")
def get_weather():
    response = helpers.call_api(weather_api_url, headers, TIMEOUT, logger).json()
    return jsonify(response), 200
