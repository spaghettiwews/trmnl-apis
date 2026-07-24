import logging
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from flask import Blueprint, jsonify, request

from blueprints.deutsch import get_random_word
from blueprints.hackernews import fetch_headlines
from blueprints.photos import get_photos
from blueprints.todos import fetch_from_calendar, generate_countdowns
from blueprints.weather import fetch_weather

logger = logging.getLogger(__name__)

merge_bp = Blueprint("merge", __name__, url_prefix="/")

# Maps the query param value (e.g. "api/weather") to a callable that returns
# plain Python data. No HTTP calls back to self — eliminates the worker deadlock.
DISPATCH = {
    "api/weather": fetch_weather,
    "api/headlines": fetch_headlines,
    "api/photos": lambda: random.choice(get_photos()),
    "api/calendar": fetch_from_calendar,
    "api/countdowns": generate_countdowns,
    "api/words": get_random_word,
}


@merge_bp.route("/api/merge")
def merge_responses():
    result = {}

    api_string = request.args.get("apis")
    if not api_string:
        return jsonify({"error": "The 'apis' query parameter is required."}), 400

    query_args: List[str] = [
        arg.strip() for arg in api_string.split(",") if arg.strip()
    ]

    # Validate all args up front so unknown keys are reported without firing any fetch
    unknown = [arg for arg in query_args if arg not in DISPATCH]
    for arg in unknown:
        result[f"error_{arg}"] = f"Unknown API: {arg}"
        logger.warning(f"Merge requested unknown API: {arg}")

    valid_args = [arg for arg in query_args if arg in DISPATCH]

    # Fetch all valid APIs in parallel — total latency is max(times) not sum(times)
    with ThreadPoolExecutor(max_workers=len(valid_args) or 1) as executor:
        futures = {executor.submit(DISPATCH[arg]): arg for arg in valid_args}

        for future in as_completed(futures):
            arg = futures[future]
            try:
                response = future.result()
                if isinstance(response, dict):
                    collisions = [k for k in response if k in result]
                    if collisions:
                        logger.warning(
                            f"Key collision from '{arg}' — overwriting keys: {collisions}"
                        )
                    result = {**result, **response}
                else:
                    result[arg] = response
            except Exception as e:
                logger.error(f"Failed to call API {arg}: {e}")
                result[f"error_{arg}"] = f"Failed to call API {arg}: {str(e)}"

    return jsonify(result), 200
