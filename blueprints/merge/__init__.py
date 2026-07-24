import logging
import os
from typing import List

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

import helpers

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

BASE_API_URL = os.getenv("BASE_API_URL")
TIMEOUT = int(os.getenv("TIMEOUT", "60"))

merge_bp = Blueprint("merge", __name__, url_prefix="/")
headers = {}


@merge_bp.route("/api/merge")
def merge_responses():
    result = {}

    api_string = request.args.get("apis")
    if not api_string:
        return jsonify({"error": "The 'apis' query parameter is required."}), 400

    query_args: List[str] = [
        arg.strip() for arg in api_string.split(",") if arg.strip()
    ]

    for arg in query_args:
        try:
            response = helpers.call_api(
                f"{BASE_API_URL}/{arg}", headers, TIMEOUT, logger
            ).json()
            result = {**result, **response}

        except Exception as e:
            result[f"error"] = f"Failed to call API {BASE_API_URL}/{arg}: {str(e)}"

    return jsonify(result), 200
