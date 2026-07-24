import logging
import os

from flask import Blueprint, jsonify

import helpers

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

hackernews_bp = Blueprint("hackernews", __name__, url_prefix="/")

TIMEOUT = int(os.getenv("TIMEOUT", "60"))


def fetch_headlines() -> list:
    """
    Fetches top story ids and headlines from HN.
    """
    logger.info("Attempting to fetch HN stories")

    ids = helpers.call_api(
        "https://hacker-news.firebaseio.com/v0/topstories.json",
        "",
        TIMEOUT,
        logger,
    ).json()

    headlines = []
    for id in ids[:10]:
        headlines.append(
            helpers.call_api(
                f"https://hacker-news.firebaseio.com/v0/item/{id}.json",
                "",
                TIMEOUT,
                logger,
            ).json()
        )

    return headlines


@hackernews_bp.route("/api/headlines")
def get_headlines():
    try:
        return jsonify(fetch_headlines()), 200
    except helpers.ApiCallError as e:
        return jsonify({"error": str(e)}), e.status_code
