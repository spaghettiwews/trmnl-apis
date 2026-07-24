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


@hackernews_bp.route("/api/headlines")
def get_headlines():
    """
    Fetches top story ids and headlines from HN.
    """

    logger.info(f"Attempting to fetch HN stories")

    ids = helpers.call_api(
        "https://hacker-news.firebaseio.com/v0/topstories.json",
        "",
        TIMEOUT,
        logger,
    )
    headlines = []

    for id in ids.json()[:10]:
        headlines.append(
            helpers.call_api(
                f"https://hacker-news.firebaseio.com/v0/item/{id}.json",
                "",
                TIMEOUT,
                logger,
            ).json()
        )

    return jsonify(headlines), 200
